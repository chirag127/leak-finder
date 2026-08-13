"""Detector 3: Price-creep — recurring debits whose amount has increased over time.

Uses cadence detection directly (doesn't require amount consistency) so that
a subscription that has drifted in price is still identified.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date

from leak_finder.detectors.subscriptions import _payee_key, _months_between, SubscriptionHit
from leak_finder.models import Account, Transaction


@dataclass
class PriceCreepHit:
    subscription: SubscriptionHit
    first_amount: Decimal
    last_amount: Decimal
    increase_pct: float

    @property
    def account_name(self) -> str:
        return self.subscription.account_name


def _detect_cadence_groups(
    account: Account,
    min_occurrences: int = 3,
    cadence_days: tuple[int, int] = (20, 40),
) -> list[list[Transaction]]:
    """Group debits by payee + monthly cadence, regardless of amount consistency."""
    debits = [t for t in account.transactions if t.is_debit]
    groups: dict[str, list[Transaction]] = {}
    for t in debits:
        k = _payee_key(t.narration)
        groups.setdefault(k, []).append(t)

    result = []
    for txns in groups.values():
        if len(txns) < min_occurrences:
            continue
        txns = sorted(txns, key=lambda t: t.date)
        gaps = [_months_between(txns[i].date, txns[i + 1].date) for i in range(len(txns) - 1)]
        monthly_gaps = [g for g in gaps if cadence_days[0] / 30 <= g <= cadence_days[1] / 30]
        if len(monthly_gaps) >= max(1, len(gaps) * 0.5):
            result.append(txns)
    return result


def detect_price_creep(
    account: Account,
    min_increase_pct: float = 5.0,
) -> list[PriceCreepHit]:
    groups = _detect_cadence_groups(account)
    hits = []
    for txns in groups:
        first = txns[0].amount
        last = txns[-1].amount
        if first == 0:
            continue
        pct = float((last - first) / first) * 100
        if pct >= min_increase_pct:
            key = _payee_key(txns[0].narration)
            avg = Decimal(str(round(sum(float(t.amount) for t in txns) / len(txns), 2)))
            sub = SubscriptionHit(
                payee_key=key,
                occurrences=txns,
                account_name=account.name,
                avg_amount=avg,
            )
            hits.append(PriceCreepHit(
                subscription=sub,
                first_amount=first,
                last_amount=last,
                increase_pct=round(pct, 1),
            ))
    return hits
