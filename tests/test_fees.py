"""Tests for fee detector."""

import pytest
from decimal import Decimal
from tests.fixtures import make_fee_account
from leak_finder.detectors.fees import detect_fees, fee_total


def test_detects_amb_penalty():
    acc = make_fee_account()
    hits = detect_fees(acc)
    categories = [h.category for h in hits]
    assert "Minimum Balance Penalty" in categories


def test_detects_gst_on_charges():
    acc = make_fee_account()
    hits = detect_fees(acc)
    categories = [h.category for h in hits]
    assert "GST on Charges" in categories


def test_detects_sms_fee():
    acc = make_fee_account()
    hits = detect_fees(acc)
    categories = [h.category for h in hits]
    assert "SMS Alert Fee" in categories


def test_detects_atm_charge():
    acc = make_fee_account()
    hits = detect_fees(acc)
    categories = [h.category for h in hits]
    assert "ATM Charge" in categories


def test_detects_cheque_fee():
    acc = make_fee_account()
    hits = detect_fees(acc)
    categories = [h.category for h in hits]
    assert "Cheque Book Fee" in categories


def test_no_false_positive_on_salary():
    acc = make_fee_account()
    hits = detect_fees(acc)
    # salary credit should not be flagged
    narrations = [h.transaction.narration for h in hits]
    assert not any("SALARY" in n for n in narrations)


def test_fee_total():
    acc = make_fee_account()
    hits = detect_fees(acc)
    total = fee_total(hits)
    # AMB x2 + GST x2 + SMS + ATM + Cheque = 590+590+18+18+25+150+500 = 1891
    assert total == Decimal("1891.00")


def test_only_debits_flagged():
    acc = make_fee_account()
    hits = detect_fees(acc)
    for h in hits:
        assert h.transaction.is_debit
