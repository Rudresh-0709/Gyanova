from __future__ import annotations

import asyncio
import threading
from copy import deepcopy
from queue import Queue
from typing import Any, Coroutine, TypeVar

try:
    from app.services.icon_selector import select_icons_batch
except ImportError:
    from ...icon_selector import select_icons_batch  # type: ignore

try:
    from app.services.node.slides.gyml.image_generator import ImageGenerator
except ImportError:
    from ..slides.gyml.image_generator import ImageGenerator  # type: ignore

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result_queue: Queue[tuple[bool, Any]] = Queue(maxsize=1)

    def _runner() -> None:
        try:
            value = asyncio.run(coro)
            result_queue.put((True, value))
        except Exception as exc:  # pragma: no cover - error path
            result_queue.put((False, exc))

    worker = threading.Thread(target=_runner, daemon=True)
    worker.start()
    worker.join()
    ok, payload = result_queue.get()
    if ok:
        return payload
    raise payload


def _get_payload(slide_obj: dict) -> tuple[dict, str]:
    if isinstance(slide_obj.get("contentBlocks"), list):
        return slide_obj, "root"

    gyml_content = slide_obj.get("gyml_content")
    if isinstance(gyml_content, dict) and isinstance(gyml_content.get("contentBlocks"), list):
        return gyml_content, "gyml_content"

    visual_content = slide_obj.get("visual_content")
    if isinstance(visual_content, dict) and isinstance(visual_content.get("contentBlocks"), list):
        return visual_content, "visual_content"

    return slide_obj, "root"


def _iter_image_blocks(content_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        block
        for block in content_blocks
        if isinstance(block, dict) and str(block.get("type") or "").strip().lower() == "image"
    ]


def _is_concept_image(block: dict[str, Any]) -> bool:
    is_accent = bool(block.get("is_accent", False))
    return not is_accent


def _ensure_unique_icons(icons: list[str]) -> list[str]:
    used: set[str] = set()
    fallback = [
        "ri-lightbulb-line",
        "ri-compass-3-line",
        "ri-shapes-line",
        "ri-focus-3-line",
        "ri-puzzle-line",
        "ri-flag-line",
        "ri-rocket-line",
    ]
    out: list[str] = []
    fallback_idx = 0
    for icon in icons:
        candidate = str(icon or "").strip() or "ri-circle-line"
        if candidate in used:
            while fallback_idx < len(fallback) and fallback[fallback_idx] in used:
                fallback_idx += 1
            candidate = fallback[fallback_idx] if fallback_idx < len(fallback) else f"ri-circle-line-{len(used)}"
            fallback_idx += 1
        used.add(candidate)
        out.append(candidate)
    return out


def _fill_missing_icons(payload: dict[str, Any], topic: str) -> None:
    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list):
        return

    targets: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        items = block.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            icon_name = str(item.get("icon_name") or "").strip().lower()
            if icon_name and icon_name != "auto":
                continue
            targets.append((block, item))

    if not targets:
        return

    icon_inputs = []
    for _, item in targets:
        icon_inputs.append(
            {
                "heading": str(item.get("heading") or item.get("title") or item.get("label") or "Concept").strip(),
                "description": str(item.get("description") or "").strip(),
            }
        )

    selected = select_icons_batch(
        icon_inputs,
        context={
            "topic": str(topic or "").strip(),
            "purpose": "v2_media_enrichment",
        },
    )
    selected = _ensure_unique_icons(selected)

    for idx, (_, item) in enumerate(targets):
        if idx < len(selected):
            item["icon_name"] = selected[idx]


def _remove_accent_images(payload: dict[str, Any]) -> None:
    payload.pop("accentImagePrompt", None)
    payload.pop("heroImagePrompt", None)
    payload.pop("imagePrompt", None)

    blocks = payload.get("contentBlocks", [])
    if not isinstance(blocks, list):
        return

    filtered: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if str(block.get("type") or "").strip().lower() == "image" and bool(block.get("is_accent", False)):
            continue
        filtered.append(block)
    payload["contentBlocks"] = filtered


def enrich_slide_media_sync(slide_obj: dict, topic: str, image_layout: str) -> dict:
    enriched = deepcopy(slide_obj)
    payload, payload_key = _get_payload(enriched)

    content_blocks = payload.get("contentBlocks", [])
    if not isinstance(content_blocks, list):
        return enriched

    non_accent_exists = False
    for block in _iter_image_blocks(content_blocks):
        if not _is_concept_image(block):
            continue

        prompt = str(
            block.get("imagePrompt")
            or block.get("prompt")
            or payload.get("imagePrompt")
            or payload.get("heroImagePrompt")
            or payload.get("accentImagePrompt")
            or f"Concept image for {topic}"
        ).strip()

        url = run_async(
            ImageGenerator.generate_accent_image(
                prompt=prompt,
                layout=str(image_layout or payload.get("image_layout") or "blank").strip().lower(),
                topic=str(topic or payload.get("title") or "Topic").strip(),
            )
        )

        if url:
            block["src"] = url
        block["is_accent"] = False
        non_accent_exists = True

    if non_accent_exists:
        _remove_accent_images(payload)

    _fill_missing_icons(payload, topic=topic)

    if payload_key == "gyml_content":
        enriched["gyml_content"] = payload
        if isinstance(enriched.get("visual_content"), dict):
            enriched["visual_content"] = deepcopy(payload)
    elif payload_key == "visual_content":
        enriched["visual_content"] = payload
        if isinstance(enriched.get("gyml_content"), dict):
            enriched["gyml_content"] = deepcopy(payload)
    else:
        enriched = payload

    return enriched
