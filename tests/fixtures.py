"""Synthetic statement fixture builder — no real data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from leak_finder.models import Account, Transaction


def make_txn(
    d: str,
    amount: str,
    dr_cr: str,
    narration: str,
    balance: str | None = None,
    source: str = "test_account",
) -> Transaction:
    return Transaction(
        date=date.fromisoformat(d),
        amount=Decimal(amount),
        dr_cr=dr_cr,
        narration=narration,
        balance=Decimal(balance) if balance else None,
        source_file=source,
    )


def make_fee_account() -> Account:
    """Account with planted bank fees."""
    return Account(
        name="hdfc_savings",
        transactions=[
            make_txn("2024-01-15", "590.00", "DR", "AMB CHRG INC GST JAN24", "45000.00"),
            make_txn("2024-01-16", "18.00",  "DR", "GST ON CHG JAN24",        "44982.00"),
            make_txn("2024-01-20", "25.00",  "DR", "SMS ALERT CHG Q4",        "44957.00"),
            make_txn("2024-02-15", "590.00", "DR", "AMB CHRG INC GST FEB24",  "44367.00"),
            make_txn("2024-02-16", "18.00",  "DR", "GST ON CHG FEB24",        "44349.00"),
            make_txn("2024-03-01", "50000.00", "CR", "SALARY MARCH",          "94349.00"),
            make_txn("2024-03-10", "150.00", "DR", "ATM CHG DECLINE FEE",     "94199.00"),
            make_txn("2024-03-12", "500.00", "DR", "CHEQUE BOOK ISSUE FEE",   "93699.00"),
        ],
    )


def make_subscription_account() -> Account:
    """Account with planted subscriptions."""
    return Account(
        name="icici_current",
        transactions=[
            # Netflix-like subscription, monthly, consistent
            make_txn("2024-01-10", "649.00", "DR", "NETFLIX SUBSCRIPTION AUTO DEBIT 123456", "20000.00"),
            make_txn("2024-02-10", "649.00", "DR", "NETFLIX SUBSCRIPTION AUTO DEBIT 234567", "19351.00"),
            make_txn("2024-03-10", "649.00", "DR", "NETFLIX SUBSCRIPTION AUTO DEBIT 345678", "18702.00"),
            make_txn("2024-04-10", "649.00", "DR", "NETFLIX SUBSCRIPTION AUTO DEBIT 456789", "18053.00"),
            # Spotify, monthly
            make_txn("2024-01-05", "119.00", "DR", "SPOTIFY INDIA AUTO DEBIT 111",  "20000.00"),
            make_txn("2024-02-05", "119.00", "DR", "SPOTIFY INDIA AUTO DEBIT 222",  "19881.00"),
            make_txn("2024-03-05", "119.00", "DR", "SPOTIFY INDIA AUTO DEBIT 333",  "19762.00"),
            # salary credit
            make_txn("2024-01-01", "50000.00", "CR", "SALARY JAN", "70000.00"),
        ],
    )


def make_price_creep_account() -> Account:
    """Account where a subscription increased in price."""
    return Account(
        name="axis_salary",
        transactions=[
            make_txn("2023-10-15", "199.00", "DR", "HOTSTAR PREMIUM ANNUAL 1001", "30000.00"),
            make_txn("2023-11-15", "199.00", "DR", "HOTSTAR PREMIUM ANNUAL 1002", "29801.00"),
            make_txn("2023-12-15", "199.00", "DR", "HOTSTAR PREMIUM ANNUAL 1003", "29602.00"),
            make_txn("2024-01-15", "249.00", "DR", "HOTSTAR PREMIUM ANNUAL 1004", "29353.00"),
            make_txn("2024-02-15", "299.00", "DR", "HOTSTAR PREMIUM ANNUAL 1005", "29054.00"),
            make_txn("2024-01-01", "80000.00", "CR", "SALARY JAN", "109054.00"),
        ],
    )


def make_dormant_account() -> Account:
    """Account with no recent activity and tiny balance."""
    return Account(
        name="old_savings_kotak",
        transactions=[
            make_txn("2023-06-01", "10000.00", "CR", "TRANSFER IN",  "10000.00"),
            make_txn("2023-06-05", "9900.00",  "DR", "TRANSFER OUT", "100.00"),
        ],
    )


def make_duplicate_account() -> Account:
    """Account with double-charge within same day."""
    return Account(
        name="sbi_current",
        transactions=[
            make_txn("2024-03-01", "299.00", "DR", "AMAZON PRIME RENEWAL 9999", "5000.00"),
            make_txn("2024-03-01", "299.00", "DR", "AMAZON PRIME RENEWAL 9999", "4701.00"),
            make_txn("2024-03-02", "50000.00", "CR", "SALARY", "54701.00"),
        ],
    )


def make_combined_account() -> Account:
    """Single account with all leak types planted."""
    txns = (
        make_fee_account().transactions
        + make_subscription_account().transactions
        + make_duplicate_account().transactions
    )
    for t in txns:
        t.source_file = "combined"
    return Account(name="combined", transactions=sorted(txns, key=lambda t: t.date))
