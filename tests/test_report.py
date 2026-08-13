"""Tests for report builder and JSON/CSV serialisation."""

from decimal import Decimal
from tests.fixtures import (
    make_fee_account,
    make_subscription_account,
    make_dormant_account,
    make_duplicate_account,
    make_combined_account,
)
from leak_finder.report import build_report, report_to_json, report_to_dict
from leak_finder.csv_export import report_to_csv
import json


def test_report_grand_fee_total():
    report = build_report([make_fee_account()])
    assert report.grand_fee_total == Decimal("1891.00")


def test_report_has_subscriptions():
    report = build_report([make_subscription_account()])
    assert report.grand_subscription_total > 0


def test_report_json_serialisable():
    report = build_report([make_fee_account(), make_subscription_account()])
    data = json.loads(report_to_json(report))
    assert "grand_fee_total" in data
    assert "accounts" in data
    assert len(data["accounts"]) == 2


def test_report_csv_has_header():
    report = build_report([make_fee_account()])
    csv_text = report_to_csv(report)
    assert csv_text.startswith("account,type,date,amount,narration,detail")


def test_report_csv_contains_fee_rows():
    report = build_report([make_fee_account()])
    csv_text = report_to_csv(report)
    assert "fee" in csv_text


def test_multi_account_report():
    accounts = [
        make_fee_account(),
        make_subscription_account(),
        make_dormant_account(),
        make_duplicate_account(),
    ]
    report = build_report(accounts)
    assert len(report.accounts) == 4
    assert report.grand_total > 0


def test_combined_account_detects_all():
    acc = make_combined_account()
    report = build_report([acc])
    ar = report.accounts[0]
    assert ar.fees
    assert ar.subscriptions
    assert ar.duplicates
