# leak-finder

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/leak-finder.svg)](https://pypi.org/project/leak-finder/)

**Local-first CLI that finds money leaks in Indian bank statements (PDFs).**
Point it at a folder of bank statement PDFs → get a report of fees, forgotten subscriptions, price-creep, dormant accounts, and double-charges.

100% local. No data leaves your machine. No signup. No cloud.

---

## What it detects

| Detector | What it finds |
|---|---|
| Silent fees | AMB/NMC penalties, SMS-alert fees, ATM charges, Demat AMC, GST on charges, cheque fees, etc. |
| Subscriptions | Same payee + similar amount on a monthly cadence |
| Price creep | A recurring debit whose amount increased over time |
| Dormancy | Accounts with no activity for N months; tiny stranded balances |
| Duplicates | Same amount + payee debited twice within a short window (IndusInd-style double SMS charges) |

## Install

```bash
# with uv (recommended)
uv tool install leak-finder

# or pip
pip install leak-finder
```

## Usage

```bash
# Scan all PDFs in a folder, rich terminal report
leak-finder scan ~/Downloads/statements/

# Password-protected PDFs (same password for all)
leak-finder scan ~/Downloads/statements/ --password ABCDE1234F

# Machine-readable JSON
leak-finder scan ~/Downloads/statements/ --json

# CSV export
leak-finder scan ~/Downloads/statements/ --csv

# Write report to file
leak-finder scan ~/Downloads/statements/ --out report.json
leak-finder scan ~/Downloads/statements/ --out report.csv

# Tune thresholds
leak-finder scan ~/Downloads/statements/ --dormancy-months 3 --tiny-balance 1000
```

## Sample output

```
╭─ Money Leak Report · 2024-06-01 ─────────────────────────────────────────────╮
│ Grand total leaked: ₹5,432.00  (fees ₹1,891.00 | subs ₹2,596.00 | dupes ₹299.00) │
╰───────────────────────────────────────────────────────────────────────────────╯

──────────────────────── hdfc_savings ─────────────────────────────────────────

 Silent fees  (₹1,891.00)
 Date        Category                  Narration                    Amount
 2024-01-15  Minimum Balance Penalty   AMB CHRG INC GST JAN24      ₹590.00
 2024-01-16  GST on Charges            GST ON CHG JAN24             ₹18.00
 2024-01-20  SMS Alert Fee             SMS ALERT CHG Q4             ₹25.00
 2024-02-15  Minimum Balance Penalty   AMB CHRG INC GST FEB24      ₹590.00
 2024-03-10  ATM Charge                ATM CHG DECLINE FEE         ₹150.00
 2024-03-12  Cheque Book Fee           CHEQUE BOOK ISSUE FEE       ₹500.00

 Action: Dispute / write to bank for fee reversal.

──────────────────────── sbi_current ──────────────────────────────────────────

 Possible double-charges  (₹299.00)
 Amount    Count  Dates                    Narration
 ₹299.00   2      2024-03-01, 2024-03-01   AMAZON PRIME RENEWAL 9999

 Action: Raise dispute for extra debit(s).
```

## Supported statement formats

Uses `pdfplumber` table extraction first, then regex line-scan fallback.
Works with most Indian bank statements that have tabular layouts:
HDFC, ICICI, SBI, Axis, Kotak, IndusInd, YES Bank, PNB, BOI, IDFC, Federal.

Encrypted PDFs: pass `--password` (same password for all files in the folder).
Per-file passwords → decrypt manually first.

## Privacy

All processing is local. No network calls. PDFs and output stay on your machine.
The tool has no telemetry, no analytics, no callbacks.

## Development

```bash
git clone https://github.com/chirag127/leak-finder
cd leak-finder
uv venv && uv pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
