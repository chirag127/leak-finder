"""Tests for CLI using Click's test runner."""

import json
from pathlib import Path

from click.testing import CliRunner
from leak_finder.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_scan_json(monkeypatch, tmp_path):
    """Scan command with mocked parse_folder -> JSON output."""
    from tests.fixtures import make_fee_account, make_subscription_account

    def mock_parse_folder(folder, password=None):
        return [make_fee_account(), make_subscription_account()]

    monkeypatch.setattr("leak_finder.cli.parse_folder", mock_parse_folder)

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    # CliRunner merges stderr into output; strip lines before the JSON object
    json_start = result.output.index("{")
    data = json.loads(result.output[json_start:])
    assert data["grand_fee_total"] > 0
    assert len(data["accounts"]) == 2


def test_cli_scan_csv(monkeypatch, tmp_path):
    from tests.fixtures import make_fee_account

    def mock_parse_folder(folder, password=None):
        return [make_fee_account()]

    monkeypatch.setattr("leak_finder.cli.parse_folder", mock_parse_folder)

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--csv"])
    assert result.exit_code == 0
    assert "fee" in result.output


def test_cli_scan_rich(monkeypatch, tmp_path):
    from tests.fixtures import make_fee_account

    def mock_parse_folder(folder, password=None):
        return [make_fee_account()]

    monkeypatch.setattr("leak_finder.cli.parse_folder", mock_parse_folder)

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path)])
    assert result.exit_code == 0


def test_cli_scan_no_transactions(monkeypatch, tmp_path):
    def mock_parse_folder(folder, password=None):
        return []

    monkeypatch.setattr("leak_finder.cli.parse_folder", mock_parse_folder)

    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path)])
    assert result.exit_code == 1


def test_cli_scan_out_json(monkeypatch, tmp_path):
    from tests.fixtures import make_fee_account

    def mock_parse_folder(folder, password=None):
        return [make_fee_account()]

    monkeypatch.setattr("leak_finder.cli.parse_folder", mock_parse_folder)

    out_file = tmp_path / "report.json"
    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path), "--out", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "grand_fee_total" in data
