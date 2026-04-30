from __future__ import annotations

from typing import Any, Dict

try:
    from app.services.node.v2.gyml_generator_v2 import _build_fallback_slide
except ImportError:
    from ..gyml_generator_v2 import _build_fallback_slide  # type: ignore

from .llm_caller import call_openai_for_json
from .post_processor import post_process_payload
from .prompt_builder import build_generation_prompt


def generate_gyml_v2(plan_item: Dict[str, Any]) -> Dict[str, Any]:
    prompt_context = build_generation_prompt(plan_item)
    payload = call_openai_for_json(prompt_context.prompt)

    if not isinstance(payload, dict):
        payload = _build_fallback_slide(plan_item)

    return post_process_payload(
        payload,
        plan_item,
        prompt_context,
        _build_fallback_slide,
    )
