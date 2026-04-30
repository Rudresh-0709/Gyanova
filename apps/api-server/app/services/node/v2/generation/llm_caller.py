from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    from app.services.llm.model_loader import load_openai
except ImportError:
    from ....llm.model_loader import load_openai  # type: ignore


def _clean_json(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _safe_json_loads(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        return json.loads(_clean_json(raw))
    except Exception:
        return None


def call_openai_for_json(prompt: str) -> Optional[Dict[str, Any]]:
    payload = None
    try:
        llm = load_openai()
        response = llm.invoke([{"role": "user", "content": prompt}])
        payload = _safe_json_loads(str(response.content or ""))
    except Exception:
        payload = None
    return payload
