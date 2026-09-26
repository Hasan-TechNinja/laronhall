"""
Stripe Connect helpers for Event Creators.

Moved from shop/stripe_connect.py so the banking setup feature is
properly scoped to event creators instead of shop creators.

Banking-only flow
-----------------
We use ``type="express"`` accounts but pre-fill as much personal data as
possible (name, email, phone) so Stripe skips the identity / social steps
and lands the creator directly on the **bank account** entry screen.

We also pass ``prefill`` / ``collection_options`` to restrict what Stripe
asks for to payout-related fields only.
"""

import logging
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------------------------
# Account helpers
# ---------------------------------------------------------------------------

def get_or_create_connect_account(user):
    """
    Retrieve an existing Stripe Express account for the event creator or
    create a new one with only the ``transfers`` capability.

    We pre-fill as much identity data as we have so Stripe's hosted
    onboarding skips social / profile screens and drops the creator
    straight onto bank-account entry.
    """
    if user.stripe_connect_account_id:
        try:
            account = stripe.Account.retrieve(user.stripe_connect_account_id)
            return account
        except stripe.error.StripeError as exc:
            logger.warning(
                "Could not retrieve Stripe account %s: %s",
                user.stripe_connect_account_id,
                exc,
            )

    # Build the minimal account payload
    account_data = {
        "type": "express",
        "country": "US",
        "capabilities": {
            "transfers": {"requested": True},
        },
        "business_type": "individual",
        "settings": {
            # Ask Stripe to skip everything except payouts / bank account setup
            "payouts": {
                "schedule": {"interval": "manual"},
            },
        },
        "metadata": {
            "user_id": str(user.id),
            "phone": str(user.phone or ""),
            "role": "event_creator",
        },
    }

    if user.email:
        account_data["email"] = user.email

    # Pre-fill individual name so Stripe skips the name entry screen
    name_parts = (user.full_name or "").strip().split(maxsplit=1)
    individual = {}
    if name_parts:
        individual["first_name"] = name_parts[0]
    if len(name_parts) == 2:
        individual["last_name"] = name_parts[1]
    if user.email:
        individual["email"] = user.email
    if user.phone:
        individual["phone"] = str(user.phone)

    if individual:
        account_data["individual"] = individual

    account = stripe.Account.create(**account_data)
    user.stripe_connect_account_id = account.id
    user.save(update_fields=["stripe_connect_account_id"])
    return account


def create_banking_onboarding_link(user, return_url=None, refresh_url=None):
    """
    Generate a single-use Stripe hosted onboarding link for the event creator.

    By pre-filling identity data and requesting ``collection_options`` that
    focus on external account / payout info, Stripe will skip the social /
    profile pages and go straight to bank account or debit-card entry.

    Parameters
    ----------
    user        : The authenticated event-creator User instance.
    return_url  : Where Stripe redirects after onboarding is complete.
    refresh_url : Where Stripe redirects if the link expires.
    """
    account = get_or_create_connect_account(user)
    default_base = getattr(settings, "FRONTEND_URL", "https://treatsislandgo.com")

    if not return_url:
        return_url = f"{default_base}/payout/return"
    if not refresh_url:
        refresh_url = f"{default_base}/payout/refresh"

    account_link_data = {
        "account": account.id,
        "refresh_url": refresh_url,
        "return_url": return_url,
        "type": "account_onboarding",
        # collection_options restricts what Stripe asks for.
        # 'eventually_due' means only fields required for payouts are shown.
        "collection_options": {
            "fields": "eventually_due",
            "future_requirements": "omit",
        },
    }

    account_link = stripe.AccountLink.create(**account_link_data)
    return account_link.url


# Keep the old name as an alias so existing callers still work
create_onboarding_link = create_banking_onboarding_link


def create_dashboard_login_link(user):
    """
    Generate a single-use Stripe dashboard login link so the event creator
    can view payouts and update their bank account.
    """
    if not user.stripe_connect_account_id:
        raise ValueError("User does not have a Stripe Connect account yet.")

    try:
        login_link = stripe.Account.create_login_link(user.stripe_connect_account_id)
        return login_link.url
    except stripe.error.StripeError:
        default_base = getattr(settings, "FRONTEND_URL", "https://treatsislandgo.com")
        return f"{default_base}/dashboard/payouts"


def sync_connect_account_status(user):
    """
    Fetch the latest verification / payout status from Stripe and sync it
    back to the local User record.

    Returns a dict with:
      - account_id
      - onboarding_completed
      - payouts_enabled
      - details_submitted
      - transfers_active
      - external_account   (last4, bank_name / brand, routing_number, status)
      - requirements_due
      - disabled_reason
      - total_creator_earnings  (annotated by the view)
    """
    if not user.stripe_connect_account_id:
        return {
            "account_id": None,
            "onboarding_completed": False,
            "payouts_enabled": False,
            "details_submitted": False,
            "external_account": None,
        }

    account = stripe.Account.retrieve(user.stripe_connect_account_id)
    details_submitted = bool(getattr(account, "details_submitted", False))
    payouts_enabled = bool(getattr(account, "payouts_enabled", False))

    requirements_obj = getattr(account, "requirements", None)
    currently_due = (
        list(getattr(requirements_obj, "currently_due", []))
        if requirements_obj
        else []
    )
    disabled_reason = (
        getattr(requirements_obj, "disabled_reason", None) if requirements_obj else None
    )

    capabilities_obj = getattr(account, "capabilities", None)
    transfers_active = False
    if capabilities_obj:
        transfers_active = getattr(capabilities_obj, "transfers", "") == "active" or (
            isinstance(capabilities_obj, dict)
            and capabilities_obj.get("transfers") == "active"
        )

    # Extract external account (bank account or debit card) details
    ext_info = None
    external_accounts_obj = getattr(account, "external_accounts", None)
    if external_accounts_obj and getattr(external_accounts_obj, "data", None):
        first_ext = external_accounts_obj.data[0]
        ext_info = {
            "id": getattr(first_ext, "id", None),
            "object": getattr(first_ext, "object", None),  # "bank_account" or "card"
            "last4": getattr(first_ext, "last4", None),
            "bank_name": getattr(first_ext, "bank_name", None),
            "brand": getattr(first_ext, "brand", None),  # for debit cards
            "routing_number": getattr(first_ext, "routing_number", None),
            "status": getattr(first_ext, "status", None),
        }

    # Persist status locally
    user.stripe_connect_onboarding_completed = details_submitted
    user.stripe_connect_payouts_enabled = payouts_enabled
    user.save(
        update_fields=[
            "stripe_connect_onboarding_completed",
            "stripe_connect_payouts_enabled",
        ]
    )

    # If payouts are now enabled, disburse any pending order payouts
    if user.stripe_connect_payouts_enabled:
        process_pending_creator_payouts(user)

    return {
        "account_id": user.stripe_connect_account_id,
        "onboarding_completed": user.stripe_connect_onboarding_completed,
        "payouts_enabled": user.stripe_connect_payouts_enabled,
        "details_submitted": details_submitted,
        "transfers_active": transfers_active,
        "external_account": ext_info,
        "requirements_due": currently_due,
        "disabled_reason": disabled_reason,
    }


# ---------------------------------------------------------------------------
# Payout helpers
# ---------------------------------------------------------------------------

def transfer_order_payout(order):
    """
    Transfer 50% of the order's product subtotal to the event creator's
    Stripe Connect account.

    If the creator hasn't completed banking setup yet the order is queued
    as ``pending_onboarding`` so it can be retried later.
    """
    if not order.fundraiser or not order.fundraiser.event:
        order.payout_status = "not_applicable"
        order.creator_payout_amount, order.treats_island_amount = (
            order.calculate_split_amounts()
        )
        order.save(
            update_fields=["creator_payout_amount", "treats_island_amount", "payout_status"]
        )
        return order

    event = order.fundraiser.event
    event_creator = event.creator
    creator_share, treats_share = order.calculate_split_amounts()
    order.creator_payout_amount = creator_share
    order.treats_island_amount = treats_share

    if not event_creator:
        order.payout_status = "not_applicable"
        order.save(
            update_fields=["creator_payout_amount", "treats_island_amount", "payout_status"]
        )
        return order

    # Queue as pending if the creator hasn't finished banking setup
    if (
        not event_creator.stripe_connect_account_id
        or not event_creator.stripe_connect_payouts_enabled
    ):
        order.payout_status = "pending_onboarding"
        order.save(
            update_fields=["creator_payout_amount", "treats_island_amount", "payout_status"]
        )
        return order

    if creator_share <= 0:
        order.payout_status = "transferred"
        order.save(
            update_fields=["creator_payout_amount", "treats_island_amount", "payout_status"]
        )
        return order

    transfer_amount_cents = int(round(float(creator_share) * 100))
    try:
        transfer = stripe.Transfer.create(
            amount=transfer_amount_cents,
            currency="usd",
            destination=event_creator.stripe_connect_account_id,
            description=(
                f"50% Revenue Payout for Order #{order.id} ({order.product.name})"
            ),
            metadata={
                "order_id": str(order.id),
                "fundraiser_id": str(order.fundraiser.id),
                "event_id": str(event.id),
                "product_name": order.product.name,
                "event_creator_user_id": str(event_creator.id),
            },
        )
        order.stripe_transfer_id = transfer.id
        order.payout_status = "transferred"
        logger.info(
            "Transferred $%s to event creator %s for Order %s",
            creator_share,
            event_creator.stripe_connect_account_id,
            order.id,
        )
    except Exception as exc:
        logger.error(
            "Failed to transfer payout for Order %s to %s: %s",
            order.id,
            event_creator.stripe_connect_account_id,
            exc,
        )
        order.payout_status = "failed"

    order.save(
        update_fields=[
            "creator_payout_amount",
            "treats_island_amount",
            "stripe_transfer_id",
            "payout_status",
        ]
    )
    return order


def process_pending_creator_payouts(user):
    """
    Find all paid orders for events created by ``user`` that are still
    awaiting a payout and execute the 50% transfer for each.
    """
    from shop.models import Order

    if not user.stripe_connect_account_id or not user.stripe_connect_payouts_enabled:
        return {"transferred_count": 0, "total_transferred": 0.0}

    pending_orders = Order.objects.filter(
        fundraiser__event__creator=user,
        is_paid=True,
        payout_status__in=["pending_onboarding", "failed", "pending"],
    )

    transferred_count = 0
    total_transferred = 0.0

    for order in pending_orders:
        transfer_order_payout(order)
        if order.payout_status == "transferred":
            transferred_count += 1
            total_transferred += float(order.creator_payout_amount)

    return {
        "transferred_count": transferred_count,
        "total_transferred": round(total_transferred, 2),
    }
