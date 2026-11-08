"""Deterministic verifier for numeric/measure comparisons.

It receives a claim string and a list of evidence dictionaries (as returned by the
EvidenceValidator). Each evidence dict must contain a ``source_quote`` field.
The verifier extracts any numeric quantity from the claim and each piece of
evidence, checks unit compatibility, and returns a tuple ``(status, details)``
where ``status`` is either ``SUPPORTED``, ``CONTRADICTED`` or ``NOT_CHECKED``.
If multiple evidences provide conflicting numeric values, ``CONTRADICTED`` is
returned.
"""

from typing import List, Tuple, Dict, Any, Optional

from .numeric_parser import parse_numeric_quantity
from .schemas import VerificationStatus


def _unit_compatible(unit_a: Optional[str], unit_b: Optional[str]) -> bool:
    """Very simple compatibility check.

    For now we only treat identical units as compatible, and also allow ``None``
    (meaning the quantity is unit‑less). In a real implementation you would add a
    conversion table (e.g., ``kg`` ↔ ``g``). This stub keeps the implementation
    deterministic without external dependencies.
    """
    if unit_a is None or unit_b is None:
        return True
    return unit_a.lower() == unit_b.lower()


def _compare_numbers(val_a: Any, val_b: Any) -> Optional[bool]:
    """Return ``True`` if numbers are equal (within tolerance), ``False`` if they
    are definitively different, or ``None`` if comparison is ambiguous.
    """
    if isinstance(val_a, tuple) or isinstance(val_b, tuple):
        # Ranges are ambiguous for deterministic checks – defer to LLM.
        return None
    try:
        tolerance = 1e-6
        return abs(float(val_a) - float(val_b)) <= tolerance
    except Exception:
        return None


def deterministic_verify(claim_text: str, evidences: List[Dict[str, Any]]) -> Tuple[VerificationStatus, Dict[str, Any]]:
    """Run deterministic numeric verification.

    Parameters
    ----------
    claim_text:
        The raw claim string extracted from the content version.
    evidences:
        List of dictionaries, each containing at least ``source_quote``.

    Returns
    -------
    (status, details):
        ``status`` is one of the ``VerificationStatus`` values that can be decided
        without LLM assistance. ``details`` may contain ``matched_evidence_ids``
        and a short ``reason`` for logging.
    """
    claim_qty = parse_numeric_quantity(claim_text)
    if not claim_qty:
        return VerificationStatus.NOT_CHECKED, {"reason": "no numeric quantity in claim"}

    compatible_ids = []
    contradictory = False
    for ev in evidences:
        ev_qty = parse_numeric_quantity(ev.get("source_quote", ""))
        if not ev_qty:
            continue
        if not _unit_compatible(claim_qty["unit"], ev_qty["unit"]):
            continue
        comp = _compare_numbers(claim_qty["value"], ev_qty["value"])
        if comp is True:
            compatible_ids.append(ev.get("id"))
        elif comp is False:
            contradictory = True
    if contradictory:
        return VerificationStatus.CONTRADICTED, {"reason": "numeric mismatch"}
    if compatible_ids:
        return VerificationStatus.SUPPORTED, {
            "matched_evidence_ids": compatible_ids,
            "reason": "numeric match",
        }
    return VerificationStatus.NOT_CHECKED, {"reason": "no matching numeric evidence"}

