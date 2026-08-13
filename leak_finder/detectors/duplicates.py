"""Detector 5: Duplicate / double debits — same amount + similar payee within a short window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from leak_finder.models import Account, Transaction
from leak_finder.detectors.subscriptions import _payee_key


@dataclass
class DuplicateHit:
    transactions: list[Transaction]
    account_name: str
    amount: Decimal
    window_days: int


def detect_duplicates(
    account: Account,
    window_days: int = 3,
    amount_tolerance: float = 0.01,  # 1% — nearly identical amounts
) -> list[DuplicateHit]:
    debits = sorted(
        [t for t in account.transactions if t.is_debit],
        key=lambda t: (t.date, t.amount),
    )

    seen: set[int] = set()
    hits: list[DuplicateHit] = []

    for i, t in enumerate(debits):
        if i in seen:
            continue
        cluster = [t]
        for j in range(i + 1, len(debits)):
            u = debits[j]
            if (u.date - t.date).days > window_days:
                break
            if abs(float(u.amount - t.amount)) / (float(t.amount) or 1) <= amount_tolerance:
                # same payee key
                if _payee_key(u.narration) == _payee_key(t.narration):
                    cluster.append(u)
                    seen.add(j)

        if len(cluster) > 1:
            seen.add(i)
            hits.append(DuplicateHit(
                transactions=cluster,
                account_name=account.name,
                amount=t.amount,
                window_days=window_days,
            ))

    return hits
