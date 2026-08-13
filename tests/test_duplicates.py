"""Tests for duplicate-debit detector."""

from decimal import Decimal
from tests.fixtures import make_duplicate_account
from leak_finder.detectors.duplicates import detect_duplicates


def test_detects_double_charge():
    acc = make_duplicate_account()
    hits = detect_duplicates(acc)
    assert len(hits) == 1


def test_duplicate_amount():
    acc = make_duplicate_account()
    hits = detect_duplicates(acc)
    assert hits[0].amount == Decimal("299.00")


def test_duplicate_count():
    acc = make_duplicate_account()
    hits = detect_duplicates(acc)
    assert len(hits[0].transactions) == 2


def test_no_false_positive_different_payees():
    """Same amount but different payee → not a duplicate."""
    from tests.fixtures import make_txn
    from leak_finder.models import Account
    acc = Account(name="test", transactions=[
        make_txn("2024-01-01", "500.00", "DR", "AMAZON PAYMENT", "10000.00"),
        make_txn("2024-01-01", "500.00", "DR", "FLIPKART PAYMENT", "9500.00"),
    ])
    hits = detect_duplicates(acc)
    assert hits == []


def test_no_false_positive_outside_window():
    """Same payee+amount but >3 days apart → not flagged."""
    from tests.fixtures import make_txn
    from leak_finder.models import Account
    acc = Account(name="test", transactions=[
        make_txn("2024-01-01", "299.00", "DR", "NETFLIX RENEWAL 1001", "10000.00"),
        make_txn("2024-02-01", "299.00", "DR", "NETFLIX RENEWAL 1001", "9701.00"),
    ])
    hits = detect_duplicates(acc)
    assert hits == []
