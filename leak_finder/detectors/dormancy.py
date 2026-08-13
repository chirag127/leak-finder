"""Detector 4: Dormant accounts and stranded/tiny balances."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from leak_finder.models import Account


@dataclass
class DormancyHit:
    account_name: str
    last_activity: date | None
    months_inactive: float
    last_balance: Decimal | None
    reason: str   # "dormant" | "tiny_balance" | "both"


def detect_dormancy(
    account: Account,
    as_of: date | None = None,
    dormancy_months: int = 6,
    tiny_balance_threshold: Decimal = Decimal("500"),
) -> list[DormancyHit]:
    if not account.transactions:
        return []

    today = as_of or date.today()
    last_activity = account.last_date
    months = (
        (today.year - last_activity.year) * 12
        + (today.month - last_activity.month)
        + (today.day - last_activity.day) / 30.0
        if last_activity else float("inf")
    )
    last_bal = account.last_balance

    dormant = months >= dormancy_months
    tiny = last_bal is not None and 0 < last_bal <= tiny_balance_threshold

    if not dormant and not tiny:
        return []

    reason = "both" if dormant and tiny else ("dormant" if dormant else "tiny_balance")
    return [DormancyHit(
        account_name=account.name,
        last_activity=last_activity,
        months_inactive=round(months, 1),
        last_balance=last_bal,
        reason=reason,
    )]
