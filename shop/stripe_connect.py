"""
Backward-compatibility shim.

Stripe Connect logic for event creators has been moved to
``event.stripe_connect``.  This module re-exports everything from there so
existing import paths inside the shop app continue to work without changes.
"""
# noqa: F401  (imported but unused — intentional re-export)
from event.stripe_connect import (
    get_or_create_connect_account,
    create_banking_onboarding_link,
    create_onboarding_link,
    create_dashboard_login_link,
    sync_connect_account_status,
    transfer_order_payout,
    process_pending_creator_payouts,
)

__all__ = [
    "get_or_create_connect_account",
    "create_banking_onboarding_link",
    "create_onboarding_link",
    "create_dashboard_login_link",
    "sync_connect_account_status",
    "transfer_order_payout",
    "process_pending_creator_payouts",
]
