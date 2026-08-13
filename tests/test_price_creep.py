"""Tests for price-creep detector."""

from tests.fixtures import make_price_creep_account
from leak_finder.detectors.price_creep import detect_price_creep


def test_detects_price_creep():
    acc = make_price_creep_account()
    hits = detect_price_creep(acc)
    assert len(hits) >= 1


def test_price_creep_amount_increase():
    acc = make_price_creep_account()
    hits = detect_price_creep(acc)
    hit = next(h for h in hits if "HOTSTAR" in h.subscription.payee_key)
    assert hit.last_amount > hit.first_amount
    assert hit.increase_pct > 0


def test_flat_subscription_not_flagged():
    """No price change → no price-creep hit."""
    from tests.fixtures import make_subscription_account
    acc = make_subscription_account()
    hits = detect_price_creep(acc)
    # all subscriptions in fixture have flat amounts
    assert hits == []
