import logging
import stripe
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_connect_account(user):
    """
    Retrieves an existing Stripe Express connected account ID for the user
    or creates a new one and saves it to the user.
    """
    if user.stripe_connect_account_id:
        try:
            account = stripe.Account.retrieve(user.stripe_connect_account_id)
            return account
        except stripe.error.StripeError as e:
            logger.warning(f"Could not retrieve Stripe account {user.stripe_connect_account_id}: {e}")

    account_data = {
        "type": "express",
        "country": "US",
        "capabilities": {
            "transfers": {"requested": True},
            "card_payments": {"requested": True},
        },
        "business_type": "individual",
        "metadata": {
            "user_id": str(user.id),
            "phone": str(user.phone or ""),
        }
    }
    if user.email:
        account_data["email"] = user.email

    name_parts = (user.full_name or "").strip().split(maxsplit=1)
    if len(name_parts) == 2:
        account_data["individual"] = {
            "first_name": name_parts[0],
            "last_name": name_parts[1],
        }
    elif len(name_parts) == 1:
        account_data["individual"] = {
            "first_name": name_parts[0],
        }

    account = stripe.Account.create(**account_data)
    user.stripe_connect_account_id = account.id
    user.save(update_fields=["stripe_connect_account_id"])
    return account


def create_onboarding_link(user, return_url=None, refresh_url=None):
    """
    Generates a single-use hosted Stripe Express onboarding link for the user.
    """
    account = get_or_create_connect_account(user)
    default_base = getattr(settings, 'FRONTEND_URL', 'https://treatsislandgo.com')
    
    if not return_url:
        return_url = f"{default_base}/payout/return"
    if not refresh_url:
        refresh_url = f"{default_base}/payout/refresh"

    account_link = stripe.AccountLink.create(
        account=account.id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return account_link.url


def create_dashboard_login_link(user):
    """
    Generates a single-use login link to the Stripe Express dashboard
    allowing the shop creator to view payouts and update bank info.
    """
    if not user.stripe_connect_account_id:
        raise ValueError("User does not have a Stripe Connect account yet.")

    login_link = stripe.Account.create_login_link(user.stripe_connect_account_id)
    return login_link.url


def sync_connect_account_status(user):
    """
    Fetches the latest account verification and payout status from Stripe
    and synchronizes it with the local User model.
    """
    if not user.stripe_connect_account_id:
        return {
            "account_id": None,
            "onboarding_completed": False,
            "payouts_enabled": False,
            "details_submitted": False,
        }

    account = stripe.Account.retrieve(user.stripe_connect_account_id)
    details_submitted = bool(getattr(account, 'details_submitted', False))
    payouts_enabled = bool(getattr(account, 'payouts_enabled', False))
    requirements_obj = getattr(account, 'requirements', None)
    currently_due = list(getattr(requirements_obj, 'currently_due', [])) if requirements_obj else []
    disabled_reason = getattr(requirements_obj, 'disabled_reason', None) if requirements_obj else None
    capabilities_obj = getattr(account, 'capabilities', None)
    transfers_active = False
    if capabilities_obj:
        transfers_active = (getattr(capabilities_obj, 'transfers', '') == 'active' or 
                            (isinstance(capabilities_obj, dict) and capabilities_obj.get('transfers') == 'active'))

    user.stripe_connect_onboarding_completed = details_submitted
    user.stripe_connect_payouts_enabled = payouts_enabled
    user.save(update_fields=["stripe_connect_onboarding_completed", "stripe_connect_payouts_enabled"])

    # If payouts or details are submitted, automatically disburse any pending order payouts
    if payouts_enabled or (details_submitted and transfers_active):
        process_pending_creator_payouts(user)

    return {
        "account_id": user.stripe_connect_account_id,
        "onboarding_completed": details_submitted,
        "payouts_enabled": payouts_enabled,
        "details_submitted": details_submitted,
        "transfers_active": transfers_active,
        "requirements_due": currently_due,
        "disabled_reason": disabled_reason,
    }


def transfer_order_payout(order):
    """
    Calculates 50% split for the shop creator (fundraiser.user) and transfers
    it to their Stripe Connect account if payouts are enabled or transfers active.
    Otherwise, marks the payout as pending_onboarding.
    """
    if not order.fundraiser:
        order.payout_status = 'not_applicable'
        order.creator_payout_amount, order.treats_island_amount = order.calculate_split_amounts()
        order.save(update_fields=['creator_payout_amount', 'treats_island_amount', 'payout_status'])
        return order

    creator = order.fundraiser.user
    creator_share, treats_share = order.calculate_split_amounts()
    order.creator_payout_amount = creator_share
    order.treats_island_amount = treats_share

    if not creator:
        order.payout_status = 'not_applicable'
        order.save(update_fields=['creator_payout_amount', 'treats_island_amount', 'payout_status'])
        return order

    # If creator hasn't submitted details, queue as pending_onboarding
    if not creator.stripe_connect_account_id or not (creator.stripe_connect_onboarding_completed or creator.stripe_connect_payouts_enabled):
        order.payout_status = 'pending_onboarding'
        order.save(update_fields=['creator_payout_amount', 'treats_island_amount', 'payout_status'])
        return order

    if creator_share <= 0:
        order.payout_status = 'transferred'
        order.save(update_fields=['creator_payout_amount', 'treats_island_amount', 'payout_status'])
        return order

    transfer_amount_cents = int(round(float(creator_share) * 100))
    try:
        transfer = stripe.Transfer.create(
            amount=transfer_amount_cents,
            currency="usd",
            destination=creator.stripe_connect_account_id,
            description=f"50% Shop Revenue Payout for Order #{order.id} ({order.product.name})",
            metadata={
                "order_id": str(order.id),
                "fundraiser_id": str(order.fundraiser.id),
                "event_id": str(order.fundraiser.event_id) if order.fundraiser.event else "",
                "product_name": order.product.name,
                "creator_user_id": str(creator.id),
            }
        )
        order.stripe_transfer_id = transfer.id
        order.payout_status = 'transferred'
        logger.info(f"Transferred ${creator_share} to {creator.stripe_connect_account_id} for Order {order.id}")
    except Exception as e:
        logger.error(f"Failed to transfer payout for Order {order.id} to {creator.stripe_connect_account_id}: {e}")
        order.payout_status = 'failed'

    order.save(update_fields=['creator_payout_amount', 'treats_island_amount', 'stripe_transfer_id', 'payout_status'])
    return order


def process_pending_creator_payouts(user):
    """
    Finds all eligible paid orders for shops owned by `user` that are awaiting
    payout and executes the 50% transfer now that the creator is onboarded.
    """
    from .models import Order
    if not user.stripe_connect_account_id or not (user.stripe_connect_payouts_enabled or user.stripe_connect_onboarding_completed):
        return {"transferred_count": 0, "total_transferred": 0.0}

    pending_orders = Order.objects.filter(
        fundraiser__user=user,
        is_paid=True,
        payout_status__in=['pending_onboarding', 'failed', 'pending']
    )

    transferred_count = 0
    total_transferred = 0.0

    for order in pending_orders:
        transfer_order_payout(order)
        if order.payout_status == 'transferred':
            transferred_count += 1
            total_transferred += float(order.creator_payout_amount)

    return {
        "transferred_count": transferred_count,
        "total_transferred": round(total_transferred, 2)
    }
