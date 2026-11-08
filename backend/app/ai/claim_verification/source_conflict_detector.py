"""Detect source conflicts among a set of validated evidence.

A conflict occurs when multiple active evidence items refer to the same
subject (e.g., product or attribute) but provide contradictory numeric values
or statements.

The implementation is deterministic: it extracts numeric quantities from each
evidence's ``source_quote`` and flags a conflict if at least two pieces of
evidence have compatible units but differing values.
"""

from typing import List, Dict, Any

from .numeric_parser import parse_numeric_quantity
from .schemas import VerificationStatus


class SourceConflictDetector:
    @staticmethod
    def detect(evidences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return conflict information.

        The returned dict contains:
        - ``conflict`` (bool)
        - ``conflicting_evidence_ids`` (list)
        - ``reason`` (str)
        """
        numeric_map: Dict[str, List[tuple]] = {}
        for ev in evidences:
            qty = parse_numeric_quantity(ev.get("source_quote", ""))
            if not qty:
                continue
            unit = qty["unit"] or ""
            key = unit.lower()
            numeric_map.setdefault(key, []).append((ev.get("id"), qty["value"]))
        for unit, values in numeric_map.items():
            distinct_vals = {v for _, v in values}
            if len(distinct_vals) > 1:
                conflict_ids = [eid for eid, _ in values]
                return {
                    "conflict": True,
                    "conflicting_evidence_ids": conflict_ids,
                    "reason": f"Contradictory numeric values for unit '{unit}'",
                }
        return {"conflict": False, "conflicting_evidence_ids": [], "reason": ""}

