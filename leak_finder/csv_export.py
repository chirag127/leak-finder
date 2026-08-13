"""CSV export helper."""

from __future__ import annotations

import csv
import io
from datetime import date

from leak_finder.report import Report


def report_to_csv(report: Report) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["account", "type", "date", "amount", "narration", "detail"])

    for ar in report.accounts:
        for h in ar.fees:
            w.writerow([ar.account_name, "fee", h.transaction.date.isoformat(),
                        float(h.transaction.amount), h.transaction.narration, h.category])

        for s in ar.subscriptions:
            for t in s.occurrences:
                w.writerow([ar.account_name, "subscription", t.date.isoformat(),
                            float(t.amount), t.narration, s.payee_key])

        for p in ar.price_creep:
            w.writerow([ar.account_name, "price_creep", p.subscription.last_date.isoformat(),
                        float(p.last_amount), p.subscription.payee_key,
                        f"+{p.increase_pct}% since {p.subscription.first_date}"])

        for d in ar.dormancy:
            w.writerow([ar.account_name, "dormancy",
                        d.last_activity.isoformat() if d.last_activity else "",
                        float(d.last_balance) if d.last_balance is not None else "",
                        "", d.reason])

        for dup in ar.duplicates:
            for t in dup.transactions[1:]:  # extra charges only
                w.writerow([ar.account_name, "duplicate", t.date.isoformat(),
                            float(t.amount), t.narration, "possible double charge"])

    return buf.getvalue()
