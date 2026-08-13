"""Transaction data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass
class Transaction:
    date: date
    amount: Decimal          # always positive
    dr_cr: Literal["DR", "CR"]
    narration: str
    balance: Decimal | None
    source_file: str = ""    # PDF filename

    @property
    def is_debit(self) -> bool:
        return self.dr_cr == "DR"


@dataclass
class Account:
    name: str                # filename stem used as account label
    transactions: list[Transaction] = field(default_factory=list)

    @property
    def last_date(self) -> date | None:
        dates = [t.date for t in self.transactions]
        return max(dates) if dates else None

    @property
    def first_date(self) -> date | None:
        dates = [t.date for t in self.transactions]
        return min(dates) if dates else None

    @property
    def last_balance(self) -> Decimal | None:
        for t in reversed(self.transactions):
            if t.balance is not None:
                return t.balance
        return None
