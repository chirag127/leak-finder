"""Aggregate all detectors and produce a structured report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from leak_finder.detectors.fees import FeeHit, detect_fees, fee_total
from leak_finder.detectors.subscriptions import SubscriptionHit, detect_subscriptions
from leak_finder.detectors.price_creep import PriceCreepHit, detect_price_creep
from leak_finder.detectors.dormancy import DormancyHit, detect_dormancy
from leak_finder.detectors.duplicates import DuplicateHit, detect_duplicates
from leak_finder.models import Account


@dataclass
class AccountReport:
    account_name: str
    fees: list[FeeHit] = field(default_factory=list)
    subscriptions: list[SubscriptionHit] = field(default_factory=list)
    price_creep: list[PriceCreepHit] = field(default_factory=list)
    dormancy: list[DormancyHit] = field(default_factory=list)
    duplicates: list[DuplicateHit] = field(default_factory=list)

    @property
    def total_fees(self) -> Decimal:
        return fee_total(self.fees)

    @property
    def total_subscriptions(self) -> Decimal:
        return sum((s.total for s in self.subscriptions), Decimal("0"))

    @property
    def total_duplicates(self) -> Decimal:
        return sum(
            (d.amount * (len(d.transactions) - 1) for d in self.duplicates),
            Decimal("0"),
        )


@dataclass
class Report:
    accounts: list[AccountReport] = field(default_factory=list)
    generated_on: str = field(default_factory=lambda: date.today().isoformat())

    @property
    def grand_fee_total(self) -> Decimal:
        return sum((a.total_fees for a in self.accounts), Decimal("0"))

    @property
    def grand_subscription_total(self) -> Decimal:
        return sum((a.total_subscriptions for a in self.accounts), Decimal("0"))

    @property
    def grand_duplicate_total(self) -> Decimal:
        return sum((a.total_duplicates for a in self.accounts), Decimal("0"))

    @property
    def grand_total(self) -> Decimal:
        return self.grand_fee_total + self.grand_subscription_total + self.grand_duplicate_total

    def top_fee_accounts(self, n: int = 5) -> list[AccountReport]:
        return sorted(self.accounts, key=lambda a: a.total_fees, reverse=True)[:n]


def build_report(accounts: list[Account]) -> Report:
    report = Report()
    for acc in accounts:
        ar = AccountReport(account_name=acc.name)
        ar.fees = detect_fees(acc)
        ar.subscriptions = detect_subscriptions(acc)
        ar.price_creep = detect_price_creep(acc)
        ar.dormancy = detect_dormancy(acc)
        ar.duplicates = detect_duplicates(acc)
        report.accounts.append(ar)
    return report


# ── JSON serialisation ────────────────────────────────────────────────────────

def _default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"not serialisable: {type(obj)}")


def _txn_dict(txn: Any) -> dict:
    return {
        "date": txn.date.isoformat(),
        "amount": float(txn.amount),
        "dr_cr": txn.dr_cr,
        "narration": txn.narration,
        "source_file": txn.source_file,
    }


def report_to_dict(report: Report) -> dict:
    accounts_out = []
    for ar in report.accounts:
        accounts_out.append({
            "account": ar.account_name,
            "total_fees": float(ar.total_fees),
            "fees": [
                {"category": h.category, **_txn_dict(h.transaction)}
                for h in ar.fees
            ],
            "total_subscriptions": float(ar.total_subscriptions),
            "subscriptions": [
                {
                    "payee": s.payee_key,
                    "occurrences": len(s.occurrences),
                    "avg_amount": float(s.avg_amount),
                    "total": float(s.total),
                    "first": s.first_date.isoformat(),
                    "last": s.last_date.isoformat(),
                }
                for s in ar.subscriptions
            ],
            "price_creep": [
                {
                    "payee": p.subscription.payee_key,
                    "first_amount": float(p.first_amount),
                    "last_amount": float(p.last_amount),
                    "increase_pct": p.increase_pct,
                }
                for p in ar.price_creep
            ],
            "dormancy": [
                {
                    "months_inactive": d.months_inactive,
                    "last_activity": d.last_activity.isoformat() if d.last_activity else None,
                    "last_balance": float(d.last_balance) if d.last_balance is not None else None,
                    "reason": d.reason,
                }
                for d in ar.dormancy
            ],
            "total_duplicates": float(ar.total_duplicates),
            "duplicates": [
                {
                    "amount": float(d.amount),
                    "count": len(d.transactions),
                    "transactions": [_txn_dict(t) for t in d.transactions],
                }
                for d in ar.duplicates
            ],
        })
    return {
        "generated_on": report.generated_on,
        "grand_fee_total": float(report.grand_fee_total),
        "grand_subscription_total": float(report.grand_subscription_total),
        "grand_duplicate_total": float(report.grand_duplicate_total),
        "grand_total": float(report.grand_total),
        "accounts": accounts_out,
    }


def report_to_json(report: Report) -> str:
    return json.dumps(report_to_dict(report), indent=2, default=_default)
