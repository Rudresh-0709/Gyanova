from __future__ import annotations

from collections import Counter


def _tail(history: list[str], window: int) -> list[str]:
    if window <= 0:
        return []
    return [str(item).strip() for item in list(history or [])[-window:] if str(item).strip()]


def _extract_family(token: str) -> str:
    text = str(token or "").strip().lower()
    if not text:
        return ""
    if ":" not in text:
        return ""
    return text.split(":", 1)[0]


def _extract_variant(token: str) -> str:
    text = str(token or "").strip().lower()
    if not text or ":" not in text:
        return ""
    return text.split(":", 1)[1]


def template_penalty(template_name: str, layout_history: list[str], window: int = 6) -> float:
    template = str(template_name or "").strip().lower()
    if not template:
        return 0.0
    recent = _tail(layout_history, window)
    penalty = 0.0
    for idx, entry in enumerate(reversed(recent)):
        entry_template = str(entry).split("|", 1)[0].strip().lower()
        if entry_template == template:
            penalty += max(0.25, 2.0 - (idx * 0.25))
    return penalty


def family_penalty(family: str, variant_history: list[str], window: int = 6) -> float:
    fam = str(family or "").strip().lower()
    if not fam:
        return 0.0
    recent = _tail(variant_history, window)
    families = [_extract_family(token) for token in recent]
    count = sum(1 for item in families if item == fam)
    if count <= 0:
        return 0.0
    return float(count) * 1.75


def variant_penalty(family: str, variant: str, variant_history: list[str], window: int = 6) -> float:
    fam = str(family or "").strip().lower()
    var = str(variant or "").strip().lower()
    if not fam or not var:
        return 0.0
    token = f"{fam}:{var}"
    recent = [item.lower() for item in _tail(variant_history, window)]
    count = sum(1 for item in recent if item == token)
    if count <= 0:
        return 0.0
    return float(count) * 2.25


def smart_layout_variant_penalty(variant: str, variant_history: list[str], window: int = 6) -> float:
    var = str(variant or "").strip().lower()
    if not var:
        return 0.0
    token = f"smart_layout:{var}"
    recent = [item.lower() for item in _tail(variant_history, window)]
    count = sum(1 for item in recent if item == token)
    if count <= 0:
        return 0.0
    return float(count) * 1.5


def template_allowed_by_hard_rule(template_name: str, layout_history: list[str], disallow_consecutive: bool = True) -> bool:
    if not disallow_consecutive:
        return True
    template = str(template_name or "").strip().lower()
    if not template:
        return True
    if not layout_history:
        return True
    last_template = str(layout_history[-1]).split("|", 1)[0].strip().lower()
    return last_template != template


def family_allowed_by_hard_rule(
    family: str,
    variant_history: list[str],
    *,
    max_in_window: int = 2,
    window: int = 4,
) -> bool:
    fam = str(family or "").strip().lower()
    if not fam:
        return True
    recent = _tail(variant_history, window)
    families = [_extract_family(token) for token in recent]
    count = sum(1 for item in families if item == fam)
    return count < max(0, int(max_in_window))