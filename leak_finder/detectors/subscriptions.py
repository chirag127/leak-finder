"""Detector 2: Subscription / recurring debits (same payee, similar amount, monthly cadence)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from leak_finder.models import Account, Transaction


def _payee_key(narration: str) -> str:
    """Normalise narration to a stable payee key."""
    s = narration.upper()
    # strip trailing reference numbers / UPI IDs / transaction IDs
    s = re.sub(r"\d+", " ", s)          # remove ALL digit sequences
    s = re.sub(r"[/_@#\-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # keep first 40 chars as key
    return s[:40]


def _months_between(a: date, b: date) -> float:
    return (b.year - a.year) * 12 + (b.month - a.month) + (b.day - a.day) / 30.0


@dataclass
class SubscriptionHit:
    payee_key: str
    occurrences: list[Transaction]
    account_name: str
    avg_amount: Decimal

    @property
    def total(self) -> Decimal:
        return sum((t.amount for t in self.occurrences), Decimal("0"))

    @property
    def first_date(self) -> date:
        return min(t.date for t in self.occurrences)

    @property
    def last_date(self) -> date:
        return max(t.date for t in self.occurrences)


def detect_subscriptions(
    account: Account,
    min_occurrences: int = 2,
    amount_tolerance: float = 0.15,   # 15 % variance still counts as "same"
    cadence_days: tuple[int, int] = (20, 40),  # monthly window
) -> list[SubscriptionHit]:
    debits = [t for t in account.transactions if t.is_debit]
    # group by payee key
    groups: dict[str, list[Transaction]] = {}
    for t in debits:
        k = _payee_key(t.narration)
        groups.setdefault(k, []).append(t)

    hits = []
    for key, txns in groups.items():
        if len(txns) < min_occurrences:
            continue
        txns = sorted(txns, key=lambda t: t.date)
        # check amount consistency
        amounts = [float(t.amount) for t in txns]
        avg = sum(amounts) / len(amounts)
        if avg == 0:
            continue
        # all amounts within tolerance of avg
        if not all(abs(a - avg) / avg <= amount_tolerance for a in amounts):
            continue
        # check cadence: at least half the gaps ≈ monthly
        gaps = [_months_between(txns[i].date, txns[i + 1].date) for i in range(len(txns) - 1)]
        monthly_gaps = [g for g in gaps if cadence_days[0] / 30 <= g <= cadence_days[1] / 30]
        if len(monthly_gaps) < max(1, len(gaps) * 0.5):
            continue
        hits.append(SubscriptionHit(
            payee_key=key,
            occurrences=txns,
            account_name=account.name,
            avg_amount=Decimal(str(round(avg, 2))),
        ))

    return hits
