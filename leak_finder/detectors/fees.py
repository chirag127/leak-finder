"""Detector 1: Recurring bank fees / silent charges.

Matches narration keywords common across Indian banks:
AMB, NMC, CHG, CHRG, FEE, PENALTY, SMS, ATM, GST ON CHG, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from leak_finder.models import Account, Transaction

# keywords → category label
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bAMB\b|\bAVERAGE\s+MIN(IMUM)?\s+BAL|\bMIN\s+BAL\b|\bNMC\b", re.I), "Minimum Balance Penalty"),
    (re.compile(r"\bSMS\s*(ALERT|CHG|CHARGE|FEE)|\bSMS\b.*\b(CHG|CHRG|FEE)\b", re.I), "SMS Alert Fee"),
    (re.compile(r"\bATM\s*(CHG|CHARGE|FEE|DECL|DECLINE)", re.I), "ATM Charge"),
    (re.compile(r"\bDEMAT\s*(AMC|FEE|CHARGE)|\bAMC\b", re.I), "Demat/AMC Fee"),
    (re.compile(r"\bNEFT\s*(CHG|CHARGE|FEE)|\bIMPS\s*(CHG|CHARGE)|\bRTGS\s*(CHG|CHARGE)", re.I), "Transfer Fee"),
    (re.compile(r"\bCHEQUE\s*(BOOK)?\s*(CHG|CHARGE|ISSUE|FEE)|\bCHQ\s*(CHG|BOOK)", re.I), "Cheque Book Fee"),
    (re.compile(r"\bDD\s*(CHG|CHARGE|ISSUE)|\bDEMAND\s*DRAFT\s*(CHG|CHARGE)", re.I), "DD Charge"),
    (re.compile(r"\bSTATEMENT\s*(CHG|CHARGE|FEE)", re.I), "Statement Fee"),
    (re.compile(r"\bINTERNET\s*(CHG|CHARGE|FEE)|\bNET\s*BANKING\s*(CHG|FEE)", re.I), "Internet Banking Fee"),
    (re.compile(r"\bGST\s*(ON\s*)?(CHG|CHARGE|FEE|TAX)|\bSERVICE\s*TAX", re.I), "GST on Charges"),
    (re.compile(r"\bPENALTY\b|\bPENL\b|\bPNLTY\b", re.I), "Penalty"),
    (re.compile(r"\b(PROC|PROCESSING)\s*(CHG|CHARGE|FEE)|\bPF\b.*\b(CHG|FEE)\b", re.I), "Processing Fee"),
    (re.compile(r"\bDR\s*CHG|\bDEBIT\s*(CHG|CHARGE)(?!\s*CARD)", re.I), "Debit Charge"),
    (re.compile(r"\bCARD\s*(ANNUAL|YEARLY)\s*(FEE|CHARGE)|\bANNUAL\s*(FEE|CHARGE).*CARD", re.I), "Card Annual Fee"),
    (re.compile(r"\bCASH\s*(HANDLING|DEPOSIT|WITHDRAWAL)\s*(CHG|CHARGE|FEE)", re.I), "Cash Handling Fee"),
    (re.compile(r"\bFOREX\s*(CHG|CHARGE|FEE)|\bFOREIGN\s*(CHG|CHARGE)", re.I), "Forex Charge"),
    (re.compile(r"\bLATE\s*(PAYMENT\s*)?(CHG|CHARGE|FEE|PENALTY)", re.I), "Late Payment Fee"),
    (re.compile(r"\bINSURANCE\s*(PREM|PREMIUM).*AUTO|\bAUTO.*DEBIT.*INSUR", re.I), "Insurance Auto-Debit"),
    (re.compile(r"\bSTAMP\s*(DUTY|CHRG|CHG)", re.I), "Stamp Duty"),
    (re.compile(r"\bLOCKER\s*(RENT|CHG|CHARGE|FEE)|\bSAFE\s*DEPOSIT", re.I), "Locker Rent"),
]


@dataclass
class FeeHit:
    transaction: Transaction
    category: str
    account_name: str


def detect_fees(account: Account) -> list[FeeHit]:
    hits = []
    for txn in account.transactions:
        if not txn.is_debit:
            continue
        narr = txn.narration
        for pat, label in _PATTERNS:
            if pat.search(narr):
                hits.append(FeeHit(transaction=txn, category=label, account_name=account.name))
                break
    return hits


def fee_total(hits: list[FeeHit]) -> Decimal:
    return sum((h.transaction.amount for h in hits), Decimal("0"))
