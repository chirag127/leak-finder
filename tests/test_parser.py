"""Tests for text-based PDF parser (synthetic text input, no real PDFs)."""

from datetime import date
from decimal import Decimal
from leak_finder.parser import _parse_date, _parse_amount, _parse_text, _parse_table


def test_parse_date_slash():
    assert _parse_date("15/01/2024") == date(2024, 1, 15)


def test_parse_date_dash():
    assert _parse_date("15-01-2024") == date(2024, 1, 15)


def test_parse_date_iso():
    assert _parse_date("2024-01-15") == date(2024, 1, 15)


def test_parse_date_short_year():
    assert _parse_date("15/01/24") == date(2024, 1, 15)


def test_parse_amount():
    assert _parse_amount("1,23,456.78") == Decimal("123456.78")


def test_parse_amount_plain():
    assert _parse_amount("649.00") == Decimal("649.00")


def test_parse_text_dr_cr():
    text = """
15/01/2024  AMB PENALTY CHG   590.00   44500.00   DR
20/01/2024  SALARY CREDIT      50000.00  94500.00   CR
"""
    txns = _parse_text(text)
    assert len(txns) >= 1
    dr_txns = [t for t in txns if t.is_debit]
    assert dr_txns


def test_parse_table_basic():
    rows = [
        ["Date", "Narration", "Debit", "Credit", "Balance"],
        ["15/01/2024", "AMB CHRG", "590.00", "", "44500.00"],
        ["20/01/2024", "SALARY", "", "50000.00", "94500.00"],
    ]
    txns = _parse_table(rows)
    assert len(txns) == 2
    assert txns[0].is_debit
    assert txns[0].amount == Decimal("590.00")
    assert txns[1].dr_cr == "CR"
    assert txns[1].amount == Decimal("50000.00")


def test_parse_table_empty():
    assert _parse_table([]) == []
    assert _parse_table([["Date", "Narration"]]) == []


def test_parse_table_no_date_col():
    rows = [["Foo", "Bar"], ["x", "y"]]
    assert _parse_table(rows) == []
