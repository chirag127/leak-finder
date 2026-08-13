"""Rich terminal renderer for leak report."""

from __future__ import annotations

from decimal import Decimal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from leak_finder.report import AccountReport, Report

_console = Console()


def _inr(amount: Decimal | float) -> str:
    return f"₹{float(amount):,.2f}"


def render(report: Report, console: Console | None = None) -> None:
    c = console or _console

    c.print(
        Panel.fit(
            f"[bold red]Money Leak Report[/bold red]  ·  {report.generated_on}\n"
            f"Grand total leaked: [bold]{_inr(report.grand_total)}[/bold]  "
            f"(fees {_inr(report.grand_fee_total)}  |  "
            f"subs {_inr(report.grand_subscription_total)}  |  "
            f"dupes {_inr(report.grand_duplicate_total)})",
            border_style="red",
        )
    )

    for ar in report.accounts:
        _render_account(ar, c)

    # Cross-account summary
    if len(report.accounts) > 1:
        tbl = Table("Account", "Fees", "Subs", "Dupes", title="Cross-account summary", box=box.SIMPLE)
        for ar in sorted(report.accounts, key=lambda a: a.total_fees, reverse=True):
            tbl.add_row(
                ar.account_name,
                _inr(ar.total_fees),
                _inr(ar.total_subscriptions),
                _inr(ar.total_duplicates),
            )
        c.print(tbl)


def _render_account(ar: AccountReport, c: Console) -> None:
    c.rule(f"[bold cyan]{ar.account_name}[/bold cyan]")

    # ── fees ─────────────────────────────────────────────────────────────────
    if ar.fees:
        tbl = Table("Date", "Category", "Narration", "Amount", title=f"Silent fees  ({_inr(ar.total_fees)})", box=box.SIMPLE)
        for h in sorted(ar.fees, key=lambda x: x.transaction.date):
            tbl.add_row(
                str(h.transaction.date),
                h.category,
                h.transaction.narration[:60],
                _inr(h.transaction.amount),
            )
        c.print(tbl)
        c.print(f"  [yellow]Action:[/yellow] Dispute / write to bank for fee reversal.")

    # ── subscriptions ─────────────────────────────────────────────────────────
    if ar.subscriptions:
        tbl = Table("Payee", "Count", "Avg/mo", "Total", "First", "Last",
                    title=f"Recurring debits  ({_inr(ar.total_subscriptions)})", box=box.SIMPLE)
        for s in sorted(ar.subscriptions, key=lambda x: x.total, reverse=True):
            tbl.add_row(
                s.payee_key[:45],
                str(len(s.occurrences)),
                _inr(s.avg_amount),
                _inr(s.total),
                str(s.first_date),
                str(s.last_date),
            )
        c.print(tbl)
        c.print("  [yellow]Action:[/yellow] Review — cancel subscriptions you no longer use.")

    # ── price creep ───────────────────────────────────────────────────────────
    if ar.price_creep:
        tbl = Table("Payee", "First", "Latest", "Increase %",
                    title="Price creep", box=box.SIMPLE)
        for p in ar.price_creep:
            tbl.add_row(
                p.subscription.payee_key[:45],
                _inr(p.first_amount),
                _inr(p.last_amount),
                f"+{p.increase_pct:.1f}%",
            )
        c.print(tbl)
        c.print("  [yellow]Action:[/yellow] Negotiate or switch provider.")

    # ── dormancy ──────────────────────────────────────────────────────────────
    if ar.dormancy:
        for d in ar.dormancy:
            bal = _inr(d.last_balance) if d.last_balance is not None else "unknown"
            c.print(f"  [bold magenta]Dormant account:[/bold magenta] {ar.account_name} — "
                    f"{d.months_inactive} months inactive, balance {bal}  [{d.reason}]")
            c.print("  [yellow]Action:[/yellow] Close or reactivate to avoid dormancy penalties.")

    # ── duplicates ────────────────────────────────────────────────────────────
    if ar.duplicates:
        tbl = Table("Amount", "Count", "Dates", "Narration",
                    title=f"Possible double-charges  ({_inr(ar.total_duplicates)})", box=box.SIMPLE)
        for d in ar.duplicates:
            dates = ", ".join(str(t.date) for t in d.transactions)
            tbl.add_row(
                _inr(d.amount),
                str(len(d.transactions)),
                dates,
                d.transactions[0].narration[:50],
            )
        c.print(tbl)
        c.print("  [yellow]Action:[/yellow] Raise dispute for extra debit(s).")

    if not (ar.fees or ar.subscriptions or ar.dormancy or ar.duplicates):
        c.print("  [green]No leaks detected.[/green]")
