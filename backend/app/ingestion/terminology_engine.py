"""
Deterministic terminology matching engine for brand governance.

Supports:
- EXACT: Matches prohibited term verbatim (optionally case-sensitive)
- WHOLE_WORD: Uses regex word boundary \\b to prevent substring matches (e.g. "cat" shouldn't match "catch")
- PHRASE: Normalized phrase matching, collapses redundant internal whitespace
"""
import re
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.brand_knowledge import TerminologyRule


@dataclass
class TerminologyMatch:
    rule_id: str
    prohibited_term: str
    preferred_term: str
    match_start: int
    match_end: int
    matched_text: str
    severity: str
    category: str
    match_type: str
    description: Optional[str] = None


class TerminologyMatcher:
    def __init__(self, rules: Optional[List[TerminologyRule]] = None):
        self.rules: List[TerminologyRule] = rules or []

    @classmethod
    def from_organisation(cls, db: Session, organisation_id: str) -> "TerminologyMatcher":
        """Load only ACTIVE terminology rules for an organisation."""
        rules = db.query(TerminologyRule).filter(
            TerminologyRule.organisation_id == organisation_id,
            TerminologyRule.status == "ACTIVE"
        ).all()
        return cls(rules=rules)

    def match_text(self, text: str) -> List[TerminologyMatch]:
        if not text or not self.rules:
            return []

        matches: List[TerminologyMatch] = []

        for rule in self.rules:
            term = rule.prohibited_term
            if not term:
                continue

            flags = 0 if rule.case_sensitive else re.IGNORECASE
            match_type = rule.match_type.upper() if rule.match_type else "EXACT"

            try:
                if match_type == "WHOLE_WORD":
                    escaped_term = re.escape(term)
                    pattern = rf"\b{escaped_term}\b"
                    regex = re.compile(pattern, flags)
                elif match_type == "PHRASE":
                    # Collapse multiple whitespaces in term to \\s+
                    words = [re.escape(w) for w in term.split() if w]
                    if not words:
                        continue
                    pattern = r"\b" + r"\s+".join(words) + r"\b"
                    regex = re.compile(pattern, flags)
                else:  # EXACT
                    pattern = re.escape(term)
                    regex = re.compile(pattern, flags)

                for m in regex.finditer(text):
                    matches.append(
                        TerminologyMatch(
                            rule_id=rule.id,
                            prohibited_term=rule.prohibited_term,
                            preferred_term=rule.preferred_term,
                            match_start=m.start(),
                            match_end=m.end(),
                            matched_text=m.group(),
                            severity=rule.severity,
                            category=rule.category,
                            match_type=match_type,
                            description=rule.description
                        )
                    )
            except Exception:
                # If regex compilation fails for any unexpected pattern, skip gracefully
                continue

        # Sort matches by start position
        matches.sort(key=lambda x: x.match_start)
        return matches

