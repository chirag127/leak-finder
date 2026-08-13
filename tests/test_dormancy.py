"""Tests for dormancy detector."""

from datetime import date
from decimal import Decimal
from tests.fixtures import make_dormant_account, make_fee_account
from leak_finder.detectors.dormancy import detect_dormancy


def test_detects_dormant_tiny_balance():
    acc = make_dormant_account()
    hits = detect_dormancy(acc, as_of=date(2024, 6, 1), dormancy_months=6)
    assert len(hits) == 1
    assert hits[0].reason in ("dormant", "both")


def test_tiny_balance_flag():
    acc = make_dormant_account()
    hits = detect_dormancy(
        acc,
        as_of=date(2023, 7, 1),   # only 1 month after last txn — not dormant
        dormancy_months=6,
        tiny_balance_threshold=Decimal("200"),
    )
    assert len(hits) == 1
    assert hits[0].reason == "tiny_balance"


def test_active_account_not_flagged():
    acc = make_fee_account()
    hits = detect_dormancy(acc, as_of=date(2024, 6, 1), dormancy_months=6)
    # fee account has activity in March 2024 → ~3 months → not dormant
    assert hits == []


def test_last_balance_reported():
    acc = make_dormant_account()
    hits = detect_dormancy(acc, as_of=date(2024, 6, 1))
    assert hits[0].last_balance == Decimal("100.00")
