"""PDF parser: extract transactions from Indian bank statement PDFs.

Strategy:
1. Try pdfplumber table extraction (works for most formatted statements).
2. Fall back to regex line-by-line scan.
Password-protected PDFs: pass `password` arg; pypdf decrypts first.
"""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from leak_finder.models import Account, Transaction

# ── date patterns ────────────────────────────────────────────────────────────
_DATE_FMTS = (
    "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
    "%d %b %Y", "%d-%b-%Y", "%d/%b/%Y",
    "%Y-%m-%d",
)

_DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}[- ][A-Za-z]{3}[- ]\d{2,4})\b"
)

# ── amount patterns ───────────────────────────────────────────────────────────
_AMT_RE = re.compile(r"[\d,]+\.\d{2}")

# ── DR/CR markers ────────────────────────────────────────────────────────────
_DR_MARKERS = re.compile(r"\b(DR|Debit|DEBIT|Dr\.?)\b", re.IGNORECASE)
_CR_MARKERS = re.compile(r"\b(CR|Credit|CREDIT|Cr\.?)\b", re.IGNORECASE)


def _parse_date(s: str) -> date | None:
    s = s.strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(s: str) -> Decimal | None:
    cleaned = s.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _decrypt_pdf_bytes(path: Path, password: str | None) -> bytes:
    """Return PDF bytes, decrypting if password given."""
    raw = path.read_bytes()
    if password:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted:
                reader.decrypt(password)
            buf = io.BytesIO()
            from pypdf import PdfWriter
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.write(buf)
            return buf.getvalue()
        except Exception:
            pass  # fall through: try pdfplumber with raw bytes + password arg
    return raw


def _extract_tables(path: Path, password: str | None) -> list[list[list[str]]]:
    """Extract all tables from PDF as list-of-rows-of-cells."""
    try:
        import pdfplumber

        kwargs: dict[str, Any] = {}
        if password:
            kwargs["password"] = password
        with pdfplumber.open(str(path), **kwargs) as pdf:
            tables = []
            for page in pdf.pages:
                for tbl in page.extract_tables():
                    tables.append([[c or "" for c in row] for row in tbl if row])
            return tables
    except Exception:
        return []


def _extract_text(path: Path, password: str | None) -> str:
    """Extract full text from PDF."""
    try:
        import pdfplumber

        kwargs: dict[str, Any] = {}
        if password:
            kwargs["password"] = password
        with pdfplumber.open(str(path), **kwargs) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        return ""


# ── table-based parsing ───────────────────────────────────────────────────────

def _col_idx(header: list[str], *candidates: str) -> int | None:
    for cand in candidates:
        for i, h in enumerate(header):
            if cand.lower() in (h or "").lower():
                return i
    return None


def _parse_table(rows: list[list[str]]) -> list[Transaction]:
    if len(rows) < 2:
        return []
    header = rows[0]
    date_col = _col_idx(header, "date", "txn date", "value date")
    narr_col = _col_idx(header, "narration", "description", "particulars", "remarks", "details")
    debit_col = _col_idx(header, "debit", "dr", "withdrawal", "dr amount", "debit amount")
    credit_col = _col_idx(header, "credit", "cr", "deposit", "cr amount", "credit amount")
    amt_col = _col_idx(header, "amount")
    dr_cr_col = _col_idx(header, "dr/cr", "type", "cr/dr")
    bal_col = _col_idx(header, "balance", "running balance", "available balance")

    if date_col is None:
        return []

    txns = []
    for row in rows[1:]:
        if len(row) <= date_col:
            continue
        d = _parse_date(row[date_col])
        if d is None:
            continue

        narration = row[narr_col].strip() if narr_col is not None and narr_col < len(row) else ""

        balance: Decimal | None = None
        if bal_col is not None and bal_col < len(row):
            balance = _parse_amount(row[bal_col])

        # determine amount + dr/cr
        amount: Decimal | None = None
        dr_cr: str | None = None

        if debit_col is not None and debit_col < len(row):
            v = _parse_amount(row[debit_col])
            if v and v > 0:
                amount = v
                dr_cr = "DR"

        if amount is None and credit_col is not None and credit_col < len(row):
            v = _parse_amount(row[credit_col])
            if v and v > 0:
                amount = v
                dr_cr = "CR"

        if amount is None and amt_col is not None and amt_col < len(row):
            amount = _parse_amount(row[amt_col])

        if dr_cr is None and dr_cr_col is not None and dr_cr_col < len(row):
            cell = (row[dr_cr_col] or "").upper()
            if "DR" in cell or "DEBIT" in cell or "W" in cell:
                dr_cr = "DR"
            elif "CR" in cell or "CREDIT" in cell or "D" in cell:
                dr_cr = "CR"

        if amount is None or dr_cr is None:
            continue

        txns.append(Transaction(
            date=d,
            amount=amount,
            dr_cr=dr_cr,
            narration=narration,
            balance=balance,
        ))

    return txns


# ── text-based fallback parsing ───────────────────────────────────────────────

def _parse_text(text: str) -> list[Transaction]:
    """Regex-based line scan fallback."""
    txns = []
    for line in text.splitlines():
        m = _DATE_RE.search(line)
        if not m:
            continue
        d = _parse_date(m.group(1))
        if not d:
            continue

        amounts = _AMT_RE.findall(line)
        if not amounts:
            continue

        # heuristic: last amount = balance (if >=2), second-last = txn amount
        if len(amounts) >= 2:
            balance = _parse_amount(amounts[-1])
            amount = _parse_amount(amounts[-2])
        else:
            amount = _parse_amount(amounts[0])
            balance = None

        if not amount or amount == 0:
            continue

        # DR/CR detection
        line_upper = line.upper()
        if _DR_MARKERS.search(line_upper):
            dr_cr = "DR"
        elif _CR_MARKERS.search(line_upper):
            dr_cr = "CR"
        else:
            dr_cr = "DR"  # assume debit if unknown

        # narration = text between date match and first amount
        narration = line[m.end():line.find(amounts[0])].strip(" :-|")

        txns.append(Transaction(
            date=d,
            amount=amount,
            dr_cr=dr_cr,
            narration=narration,
            balance=balance,
        ))

    return txns


def parse_pdf(path: str | Path, password: str | None = None) -> Account:
    """Parse a bank statement PDF and return an Account with transactions."""
    p = Path(path)
    tables = _extract_tables(p, password)

    txns: list[Transaction] = []
    for tbl in tables:
        found = _parse_table(tbl)
        if found:
            txns.extend(found)

    if not txns:
        text = _extract_text(p, password)
        txns = _parse_text(text)

    # tag source file
    name = p.stem
    for t in txns:
        t.source_file = name

    txns.sort(key=lambda t: t.date)
    return Account(name=name, transactions=txns)


def parse_folder(folder: str | Path, password: str | None = None) -> list[Account]:
    """Parse all PDFs in folder."""
    folder = Path(folder)
    accounts = []
    for pdf in sorted(folder.glob("*.pdf")):
        acc = parse_pdf(pdf, password)
        if acc.transactions:
            accounts.append(acc)
    return accounts
