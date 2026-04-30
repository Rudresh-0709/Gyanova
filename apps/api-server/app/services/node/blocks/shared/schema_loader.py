from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


def _families_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "families"


@lru_cache(maxsize=None)
def _load_schema_cached(variant: str) -> Dict[str, Any]:
    normalized_variant = str(variant or "").strip()
    if not normalized_variant:
        raise ValueError("Cannot load block schema: variant is empty.")

    families_dir = _families_dir()
    schema_dirs = sorted(families_dir.glob("*/schemas"))
    for schema_dir in schema_dirs:
        schema_path = schema_dir / f"{normalized_variant}.json"
        if not schema_path.is_file():
            continue

        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
        if not isinstance(schema, dict):
            raise ValueError(
                f"Block schema for variant '{normalized_variant}' must be a JSON object: {schema_path}"
            )
        return schema

    searched = ", ".join(str(path) for path in schema_dirs) or str(families_dir)
    raise FileNotFoundError(
        f"No block schema found for variant '{normalized_variant}'. "
        f"Searched blocks/families/*/schemas/ under: {searched}"
    )


def load_schema(variant: str) -> dict:
    """Load the schema JSON for a block variant from any family schemas directory."""
    return copy.deepcopy(_load_schema_cached(variant))
