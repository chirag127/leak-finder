"""Detectors package."""

from leak_finder.detectors.fees import detect_fees
from leak_finder.detectors.subscriptions import detect_subscriptions
from leak_finder.detectors.price_creep import detect_price_creep
from leak_finder.detectors.dormancy import detect_dormancy
from leak_finder.detectors.duplicates import detect_duplicates

__all__ = [
    "detect_fees",
    "detect_subscriptions",
    "detect_price_creep",
    "detect_dormancy",
    "detect_duplicates",
]
