"""Lightweight hallucination guard for v2 slides generated in general-knowledge mode.

When no retrieved facts are available, the LLM may still produce invented specifics
(years, percentages, named institutions, fake citations).  This module scans the
generated slide text and flags or sanitises such patterns.

Design decisions
----------------
- Only active when ``grounding_mode == "general_knowledge"`` (no research context).
- Non-destructive by default: adds a ``hallucination_risk_flags`` list to the slide
  object rather than silently removing content.
- Optionally redacts flagged sentences when ``redact=True`` is passed to the checker.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Suspicious pattern definitions
# Each tuple: (label, compiled pattern)
# ---------------------------------------------------------------------------
_SUSPICIOUS_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("year_reference", re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")),
    ("percentage", re.compile(r"\b\d+\s*%")),
    ("according_to", re.compile(r"\baccording\s+to\b", re.IGNORECASE)),
    ("study_reference", re.compile(r"\b(study|studies|research(ers)?|scientists?|experts?)\s+(show|found|suggest|prove|demonstrate)", re.IGNORECASE)),
    ("named_institution", re.compile(
        # Representative sample of frequently hallucinated institutions -- not exhaustive.
        r"\b(harvard|mit|stanford|oxford|cambridge|nasa|who|cdc|un|unicef|oecd)\b",
        re.IGNORECASE,
    )),
    ("specific_statistic", re.compile(r"\b\d[\d,.]+\s*(million|billion|trillion|thousand|percent|%)\b", re.IGNORECASE)),
    ("citation_phrase", re.compile(r"\b(published in|journal of|proc\.|proceedings of|et al\.?)\b", re.IGNORECASE)),
]

# Separator between sentences when redacting.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _extract_text_fields(slide: Dict[str, Any]) -> List[str]:
    """Collect all text strings visible inside a slide object for scanning."""
    texts: List[str] = []

    def _walk(obj: Any) -> None:
        if isinstance(obj, str):
            texts.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(slide.get("contentBlocks", []))
    _walk(slide.get("title", ""))
    _walk(slide.get("subtitle", ""))
    _walk(slide.get("narration_text", ""))
    return texts


def _scan_text(text: str) -> List[Dict[str, str]]:
    """Return a list of flag dicts for each suspicious match in *text*."""
    flags = []
    for label, pattern in _SUSPICIOUS_PATTERNS:
        for m in pattern.finditer(text):
            flags.append({"type": label, "match": m.group(0)})
    return flags


def _redact_sentence(sentence: str) -> str:
    """Replace a flagged sentence with a generic placeholder."""
    return "[content omitted — specifics could not be verified]"


def check_slide(slide: Dict[str, Any], *, redact: bool = False) -> Dict[str, Any]:
    """Scan a slide for hallucination risk patterns.

    Parameters
    ----------
    slide:
        The slide object (dict) returned by ``generate_gyml_v2``.
    redact:
        When ``True``, flagged sentences in string fields are replaced with a
        safe placeholder.  Defaults to ``False`` (flag-only, non-destructive).

    Returns
    -------
    The slide dict, augmented with:
    - ``hallucination_risk_flags``: list of flag dicts (may be empty).
    - ``hallucination_risk_score``: integer count of flagged matches.
    """
    flags: List[Dict[str, str]] = []

    for text in _extract_text_fields(slide):
        flags.extend(_scan_text(text))

    slide = dict(slide)  # shallow copy — do not mutate caller's dict
    slide["hallucination_risk_flags"] = flags
    slide["hallucination_risk_score"] = len(flags)

    if redact and flags:
        slide = _redact_slide(slide)

    return slide


def _redact_slide(slide: Dict[str, Any]) -> Dict[str, Any]:
    """Walk the slide and redact flagged sentences (best-effort, string fields only)."""

    def _redact_value(obj: Any) -> Any:
        if isinstance(obj, str):
            sentences = _SENTENCE_SPLIT.split(obj)
            cleaned = []
            for s in sentences:
                if any(p.search(s) for _, p in _SUSPICIOUS_PATTERNS):
                    cleaned.append(_redact_sentence(s))
                else:
                    cleaned.append(s)
            return " ".join(cleaned)
        if isinstance(obj, dict):
            return {k: _redact_value(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_redact_value(item) for item in obj]
        return obj

    return _redact_value(slide)  # type: ignore[return-value]
