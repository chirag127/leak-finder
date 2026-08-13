"""CLI entry point: leak-finder scan <folder> [options]"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from leak_finder import __version__
from leak_finder.parser import parse_folder
from leak_finder.report import build_report, report_to_json
from leak_finder.renderer import render
from leak_finder.csv_export import report_to_csv


@click.group()
@click.version_option(__version__, prog_name="leak-finder")
def main() -> None:
    """Local-first Indian bank statement money-leak detector."""


@main.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--password", "-p", default=None, help="PDF password (same for all files).")
@click.option("--json", "as_json", is_flag=True, help="Output full report as JSON.")
@click.option("--csv", "as_csv", is_flag=True, help="Print CSV to stdout.")
@click.option("--out", "-o", default=None, type=click.Path(path_type=Path),
              help="Write report to file (.json or .csv based on extension).")
@click.option("--dormancy-months", default=6, show_default=True,
              help="Months of inactivity to flag dormancy.")
@click.option("--tiny-balance", default=500, show_default=True,
              help="Balance <= this (INR) is flagged as stranded.")
def scan(
    folder: Path,
    password: str | None,
    as_json: bool,
    as_csv: bool,
    out: Path | None,
    dormancy_months: int,
    tiny_balance: int,
) -> None:
    """Scan all PDFs in FOLDER and report money leaks."""
    from decimal import Decimal

    def _log(msg: str) -> None:
        click.echo(msg, err=True)

    _log(f"Scanning {folder} ...")

    accounts = parse_folder(folder, password=password)
    if not accounts:
        _log("No transactions found. Check folder and PDF password.")
        sys.exit(1)

    _log(f"Parsed {sum(len(a.transactions) for a in accounts)} transactions "
         f"across {len(accounts)} account(s).")

    # patch dormancy thresholds before build
    import leak_finder.detectors.dormancy as _dorm_mod
    _orig_dormancy = _dorm_mod.detect_dormancy

    def _patched_dormancy(account, as_of=None, **_kw):
        return _orig_dormancy(
            account,
            as_of=as_of,
            dormancy_months=dormancy_months,
            tiny_balance_threshold=Decimal(str(tiny_balance)),
        )
    _dorm_mod.detect_dormancy = _patched_dormancy

    report = build_report(accounts)

    _dorm_mod.detect_dormancy = _orig_dormancy  # restore

    if as_json:
        click.echo(report_to_json(report))
    elif as_csv:
        click.echo(report_to_csv(report))
    else:
        render(report, console=Console())

    if out:
        suffix = out.suffix.lower()
        if suffix == ".csv":
            out.write_text(report_to_csv(report), encoding="utf-8")
        else:
            out.write_text(report_to_json(report), encoding="utf-8")
        _log(f"Report written -> {out}")


if __name__ == "__main__":
    main()
