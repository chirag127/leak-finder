"""Tests for subscription detector."""

from decimal import Decimal
from tests.fixtures import make_subscription_account
from leak_finder.detectors.subscriptions import detect_subscriptions


def test_detects_netflix():
    acc = make_subscription_account()
    hits = detect_subscriptions(acc)
    payees = [h.payee_key for h in hits]
    assert any("NETFLIX" in p for p in payees)


def test_detects_spotify():
    acc = make_subscription_account()
    hits = detect_subscriptions(acc)
    payees = [h.payee_key for h in hits]
    assert any("SPOTIFY" in p for p in payees)


def test_subscription_avg_amount():
    acc = make_subscription_account()
    hits = detect_subscriptions(acc)
    netflix = next(h for h in hits if "NETFLIX" in h.payee_key)
    assert netflix.avg_amount == Decimal("649.00")


def test_subscription_occurrence_count():
    acc = make_subscription_account()
    hits = detect_subscriptions(acc)
    netflix = next(h for h in hits if "NETFLIX" in h.payee_key)
    assert len(netflix.occurrences) == 4


def test_no_single_occurrence_flagged():
    """One-off debits must not be flagged."""
    from tests.fixtures import make_txn
    from leak_finder.models import Account
    acc = Account(name="test", transactions=[
        make_txn("2024-01-01", "499.00", "DR", "RANDOM PAYMENT", "10000.00"),
    ])
    hits = detect_subscriptions(acc)
    assert hits == []
