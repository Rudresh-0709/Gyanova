"""Helper utilities for building research/grounding context in v2 content generation.

This module extracts Tavily/Wikipedia retrieved facts from TutorState and produces a
safe, bounded string that the GyML generator can use for soft grounding.

Soft-grounding contract:
- If research text is present: prefer it for facts, dates, names; do not contradict it.
- If research text is absent: generate from general knowledge without inventing specifics.
"""
from __future__ import annotations

import html
import re
from typing import Any, Dict

# Minimum length (chars) for research text to be considered "meaningful".
MIN_RESEARCH_LEN: int = 100

# Default max characters to include in the grounding block to keep prompts bounded.
DEFAULT_MAX_CHARS: int = 8_000

# Header prefix injected before the research block so the LLM recognises its purpose.
_RESEARCH_HEADER = (
    "RETRIEVED FACTS — use these as the primary source for facts, dates, and names. "
    "Do NOT contradict or ignore them. Statements not supported by this text should be "
    "phrased as general or approximate (e.g. 'generally', 'often').\n\n"
)


def get_research_text(state: Dict[str, Any]) -> str:
    """Return raw research text from state, preferring the teacher-level global field."""
    raw = str(state.get("teacher_research_raw_text") or "").strip()
    if not raw:
        # Fallback: some pipelines store it under a slightly different key.
        raw = str(state.get("research_raw_text") or "").strip()
    return raw


def has_research(state: Dict[str, Any]) -> bool:
    """Return True if the state contains meaningful retrieved research."""
    return len(get_research_text(state)) >= MIN_RESEARCH_LEN


def _strip_problematic_markup(text: str) -> str:
    """Remove HTML tags and unescape HTML entities so the text is prompt-safe."""
    # Unescape HTML entities (e.g. &amp; → &)
    text = html.unescape(text)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse excess whitespace
    text = re.sub(r"\s{3,}", "\n\n", text.strip())
    return text


def build_research_context(state: Dict[str, Any], max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Return a prompt-ready research context string, or '' when no research is available.

    Args:
        state: TutorState dict (or any dict with ``teacher_research_raw_text``).
        max_chars: Maximum character count for the trimmed research body (excluding header).

    Returns:
        A non-empty string starting with _RESEARCH_HEADER when research is present,
        or an empty string when there is no meaningful research.
    """
    raw = get_research_text(state)
    if len(raw) < MIN_RESEARCH_LEN:
        return ""

    clean = _strip_problematic_markup(raw)
    if len(clean) < MIN_RESEARCH_LEN:
        return ""

    trimmed = clean[:max_chars]
    # If we cut mid-sentence, trim to last full stop to avoid confusing partial sentences.
    if len(clean) > max_chars:
        last_stop = trimmed.rfind(".")
        if last_stop > max_chars // 2:
            trimmed = trimmed[: last_stop + 1]

    return _RESEARCH_HEADER + trimmed
