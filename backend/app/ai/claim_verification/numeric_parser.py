"""Utilities to parse numeric quantities from free‑text strings.

Supported patterns:
- Simple integers/floats (e.g., "30", "3.5")
- Percentages ("20%")
- Currency with symbols ("$1,200", "₹1,499")
- Durations ("2h", "30 minutes", "1 hour 15 min")
- Weight/volume ("500g", "0.5 kg", "2 L")
- Distance ("10km", "5 miles")
- Ranges ("10‑15", "10 to 15")

The parser returns a dictionary with ``value`` (float), ``unit`` (str or ``None``) and
``raw`` (original string). If parsing fails, ``None`` is returned.
"""

import re
from typing import Optional, Dict, Any

# Simple regex patterns for common units. Extend as needed.
_NUMBER_RE = r"(?P<value>-?\d+(?:[.,]\d+)?)"
_PERCENT_RE = r"(?P<value>-?\d+(?:[.,]\d+)?)%"
_CURRENCY_RE = r"(?P<symbol>[$€£₹])\s*(?P<value>-?\d+(?:[.,]\d+)?)"
_DURATION_RE = r"(?P<value>-?\d+(?:[.,]\d+)?)\s*(?P<unit>h|hr|hour|hours|m|min|minute|minutes)"
_WEIGHT_RE = r"(?P<value>-?\d+(?:[.,]\d+)?)\s*(?P<unit>g|kg|mg|lb|lbs|oz)"
_VOLUME_RE = r"(?P<value>-?\d+(?:[.,]\d+)?)\s*(?P<unit>l|ml|cl|dl)"
_DISTANCE_RE = r"(?P<value>-?\d+(?:[.,]\d+)?)\s*(?P<unit>km|m|mi|mile|miles)"
_RANGE_RE = r"(?P<low>-?\d+(?:[.,]\d+)?)[\s-–to]{1,3}(?P<high>-?\d+(?:[.,]\d+)?)"

_PATTERNS = [
    (re.compile(_PERCENT_RE, re.IGNORECASE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": "%", "raw": m.group(0)}),
    (re.compile(_CURRENCY_RE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": m.group('symbol'), "raw": m.group(0)}),
    (re.compile(_DURATION_RE, re.IGNORECASE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": m.group('unit').lower(), "raw": m.group(0)}),
    (re.compile(_WEIGHT_RE, re.IGNORECASE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": m.group('unit').lower(), "raw": m.group(0)}),
    (re.compile(_VOLUME_RE, re.IGNORECASE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": m.group('unit').lower(), "raw": m.group(0)}),
    (re.compile(_DISTANCE_RE, re.IGNORECASE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": m.group('unit').lower(), "raw": m.group(0)}),
    (re.compile(_NUMBER_RE), lambda m: {"value": float(m.group('value').replace(',', '.')), "unit": None, "raw": m.group(0)}),
    (re.compile(_RANGE_RE), lambda m: {"value": (float(m.group('low').replace(',', '.')), float(m.group('high').replace(',', '.'))), "unit": None, "raw": m.group(0)}),
]


def _clean_number(s: str) -> str:
    """Remove thousand‑separator commas and normalize decimal point."""
    return s.replace(",", "")


def parse_numeric_quantity(text: str) -> Optional[Dict[str, Any]]:
    """Parse *text* and return a dict with ``value``, ``unit`` and ``raw``.

    Returns ``None`` when no recognizable numeric pattern is found.
    """
    if not text:
        return None
    txt = text.strip()
    for pat, builder in _PATTERNS:
        m = pat.search(txt)
        if m:
            result = builder(m)
            # Ensure proper float conversion for the ``value`` field
            if isinstance(result["value"], str):
                result["value"] = float(_clean_number(result["value"]))
            return result
    return None

