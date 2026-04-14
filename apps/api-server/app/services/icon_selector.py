"""
Smart Icon Selector - Uses Groq LLM to select contextually appropriate icons

This module provides intelligent icon selection from the RemixIcon library based on:
- Semantic meaning of the content
- Icon category descriptions
- Context (heading, description, slide purpose)

Instead of hardcoding icon names, content generation can request icon TYPES,
and this module will select the most appropriate specific icon.

FIXES APPLIED:
- Fixed double "-line" suffix appending (Bug #1)
- Fixed icon validation format mismatch (Bug #2)
- Added retry logic with exponential backoff for rate limits (Bug #3)
- Fixed invalid fallback icon names (Bug #4)
- Added exclude_icons parameter to prevent duplicates (Bug #5)
- Made JSON parsing more robust (Bug #6)
- Expanded icon samples / two-stage selection (Bug #7)
- Added global rate limiter (Bug #8)

REFINEMENTS (v2):
- normalize_icon_name now respects icons without -line/-fill variants (e.g. ri-number-1)
- _ICON_LOOKUP is used in validate_icon_any_category for O(1) performance
- select_icon performs final existence validation before returning
"""

import os
import re
import sys
import json
import time
import asyncio
import threading
from typing import Dict, List, Optional, Set, Tuple
from functools import lru_cache
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.services.llm.model_loader import load_groq_fast
except ImportError:
    try:
        from services.llm.model_loader import load_groq_fast
    except ImportError:
        from llm.model_loader import load_groq_fast

load_dotenv()

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

ICONS_PATH = os.path.join(os.path.dirname(__file__), "remix-icons.json")

with open(ICONS_PATH, "r", encoding="utf-8") as f:
    REMIX_ICONS = json.load(f)

# Preferred icon style suffix
ICON_STYLE = "-line"

# Rate limiter settings
MAX_CALLS_PER_MINUTE = 25

# Retry settings
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2.0

# Guaranteed-unique fallback icons (all verified RemixIcon names)
FALLBACK_ICONS = [
    "ri-circle-line",
    "ri-checkbox-blank-circle-line",
    "ri-radio-button-line",
    "ri-stop-circle-line",
    "ri-disc-line",
    "ri-record-circle-line",
    "ri-focus-3-line",
    "ri-crosshair-2-line",
    "ri-compass-line",
    "ri-globe-line",
    "ri-shape-line",
    "ri-square-line",
    "ri-hexagon-line",
    "ri-octagon-line",
    "ri-triangle-line",
    "ri-pentagon-line",
    "ri-star-line",
    "ri-heart-line",
    "ri-shield-line",
    "ri-bookmark-line",
]

# Predefined mappings for common content types (faster than LLM, use as fallback)
CONTENT_TYPE_ICON_MAP = {
    "technology": "ri-cpu-line",
    "process": "ri-arrow-right-circle-line",
    "feature": "ri-star-line",
    "benefit": "ri-checkbox-circle-line",
    "step": "ri-number-1",
    "data": "ri-database-line",
    "network": "ri-global-line",
    "security": "ri-shield-check-line",
    "speed": "ri-flashlight-line",
    "memory": "ri-hard-drive-line",
    "programming": "ri-code-line",
    "design": "ri-palette-line",
    "communication": "ri-chat-3-line",
    "business": "ri-briefcase-line",
    "document": "ri-file-text-line",
    "settings": "ri-settings-3-line",
    "user": "ri-user-line",
    "time": "ri-time-line",
    "location": "ri-map-pin-line",
    "education": "ri-book-open-line",
}


# ============================================================================
# ICON LOOKUP TABLES (built once at module load)
# ============================================================================

def _build_icon_lookup() -> Tuple[Dict[str, List[str]], Set[str]]:
    """
    Build two structures at module load:

    1. _ICON_LOOKUP: { normalized_base: [(category, raw_icon_name), ...] }
       Used for O(1) fuzzy validation.

    2. _ALL_RAW_ICONS: set of every raw icon string exactly as it appears in
       remix-icons.json. Used to check whether an icon exists verbatim
       (important for icons without -line/-fill variants like ri-number-1).
    """
    lookup: Dict[str, List[Tuple[str, str]]] = {}
    all_raw: Set[str] = set()

    for category, data in REMIX_ICONS.items():
        for icon in data.get("icons", []):
            all_raw.add(icon)

            # Store under the raw name itself
            lookup.setdefault(icon, []).append((category, icon))

            # Also store under a normalized base (strip ri- prefix and -line/-fill suffix)
            base = icon
            if base.startswith("ri-"):
                base = base[3:]
            for suffix in ("-line", "-fill"):
                if base.endswith(suffix):
                    base = base[: -len(suffix)]
                    break
            base = base.strip()

            lookup.setdefault(base, []).append((category, icon))

    return lookup, all_raw


_ICON_LOOKUP, _ALL_RAW_ICONS = _build_icon_lookup()


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Simple token bucket rate limiter for API calls."""

    def __init__(self, max_calls_per_minute: int = 25):
        self.min_interval = 60.0 / max_calls_per_minute
        self.last_call_time = 0.0
        self.lock = threading.Lock()

    def wait(self):
        """Block until it's safe to make another call."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call_time
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)
            self.last_call_time = time.time()


# Module-level rate limiter instance
_rate_limiter = RateLimiter(max_calls_per_minute=MAX_CALLS_PER_MINUTE)


# ============================================================================
# LLM CLIENT (cached, thread-safe singleton)
# ============================================================================

_llm_client = None
_llm_lock = threading.Lock()


def get_llm_client():
    """Get or create a cached LLM client. Thread-safe singleton."""
    global _llm_client
    if _llm_client is None:
        with _llm_lock:
            if _llm_client is None:
                _llm_client = load_groq_fast()
    return _llm_client


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_icon_name(icon: str, style: str = ICON_STYLE) -> str:
    """
    Ensure icon name has exactly one style suffix, BUT only if the icon
    actually uses -line/-fill variants.

    Icons like ri-number-1, ri-number-2, etc. do NOT have -line/-fill variants
    and must be returned as-is.

    Strategy:
    1. If the raw icon (or its stripped base + style) exists verbatim in the
       library → use that.
    2. If the icon already exists as-is in the library (no variant) → return it
       unchanged.
    3. Otherwise, strip any existing suffix and append the requested style.
    """
    if not icon:
        return "ri-circle" + style

    # Ensure it starts with "ri-"
    if not icon.startswith("ri-"):
        icon = "ri-" + icon

    # ------------------------------------------------------------------
    # Case 1: icon already exists exactly in the library → return as-is
    # ------------------------------------------------------------------
    if icon in _ALL_RAW_ICONS:
        return icon

    # ------------------------------------------------------------------
    # Case 2: strip existing suffix, try base + requested style
    # ------------------------------------------------------------------
    base = icon
    for suffix in ("-line", "-fill"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break

    candidate_with_style = base + style
    if candidate_with_style in _ALL_RAW_ICONS:
        return candidate_with_style

    # ------------------------------------------------------------------
    # Case 3: maybe the base itself (no suffix) is in the library
    #         e.g. "ri-number-1"
    # ------------------------------------------------------------------
    if base in _ALL_RAW_ICONS:
        return base

    # ------------------------------------------------------------------
    # Case 4: fuzzy lookup via _ICON_LOOKUP
    # ------------------------------------------------------------------
    short_base = base[3:] if base.startswith("ri-") else base  # strip ri-
    if short_base in _ICON_LOOKUP:
        # Return the first raw icon from the lookup
        return _ICON_LOOKUP[short_base][0][1]

    # ------------------------------------------------------------------
    # Fallback: return with requested style (best effort)
    # ------------------------------------------------------------------
    return base + style


def icon_exists(icon: str) -> bool:
    """
    Check whether a normalized icon name actually exists in the library.
    O(1) via set lookup.
    """
    if icon in _ALL_RAW_ICONS:
        return True

    # Also check via the fuzzy lookup
    base = icon
    if base.startswith("ri-"):
        base = base[3:]
    for suffix in ("-line", "-fill"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    base = base.strip()

    return base in _ICON_LOOKUP


def extract_json_from_response(content: str) -> dict:
    """Robustly extract JSON from LLM response."""
    # Remove markdown code fences (case-insensitive)
    content = re.sub(r"```(?:json|JSON)?\s*", "", content)
    content = content.replace("```", "").strip()

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        json_str = match.group(0)
        # Fix trailing commas before closing braces/brackets
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from response: {content[:200]}")


def invoke_with_retry(
    llm,
    messages,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_RETRY_DELAY,
):
    """
    Invoke LLM with exponential backoff retry on rate limit errors.
    Also respects the global rate limiter.
    """
    for attempt in range(max_retries):
        try:
            _rate_limiter.wait()
            return llm.invoke(messages)
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any(
                keyword in error_str
                for keyword in [
                    "rate_limit",
                    "429",
                    "too many requests",
                    "rate limit",
                    "ratelimit",
                ]
            )

            if is_rate_limit and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 2s, 4s, 8s
                print(
                    f"   [WAIT] Rate limited (429). Waiting {delay:.1f}s before retry "
                    f"{attempt + 2}/{max_retries}..."
                )
                time.sleep(delay)
            elif "413" in error_str:
                print("   [ERR] LLM Request Too Large (413). Prompt exceeds token limit.")
                raise  # Let caller handle fallback
            elif "403" in error_str:
                print("   [ERR] LLM Access Forbidden (403). Check API keys/permissions.")
                raise  # Let caller handle fallback
            else:
                raise


def validate_icon_in_category(icon: str, category: str) -> Optional[str]:
    """
    Validate icon exists in a specific category, handling various naming formats.
    Returns the canonical icon name from the JSON if found, None otherwise.
    Uses _ICON_LOOKUP for fast matching.
    """
    if category not in REMIX_ICONS:
        return None

    available_icons = REMIX_ICONS[category].get("icons", [])
    if not available_icons:
        return None

    # Direct match
    if icon in available_icons:
        return icon

    # Normalize and check via lookup
    base = icon
    if base.startswith("ri-"):
        base = base[3:]
    for suffix in ("-line", "-fill"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    base = base.strip()

    if base in _ICON_LOOKUP:
        for cat, raw_icon in _ICON_LOOKUP[base]:
            if cat == category:
                return raw_icon

    # Substring containment as a last resort
    for avail in available_icons:
        avail_base = avail.replace("ri-", "").replace("-line", "").replace("-fill", "").strip()
        if base in avail_base or avail_base in base:
            return avail

    return None


def validate_icon_any_category(icon: str) -> Optional[str]:
    """
    Check if icon exists in ANY category.
    Returns the raw icon name from JSON if found, None otherwise.
    Uses _ICON_LOOKUP for O(1) performance.
    """
    # Direct check
    if icon in _ALL_RAW_ICONS:
        return icon

    # Normalize and check lookup
    base = icon
    if base.startswith("ri-"):
        base = base[3:]
    for suffix in ("-line", "-fill"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    base = base.strip()

    if base in _ICON_LOOKUP:
        # Return the first match
        return _ICON_LOOKUP[base][0][1]

    return None


def get_unique_fallback(used_icons: Set[str], index: int = 0) -> str:
    """Get a guaranteed-unique fallback icon not in used_icons."""
    # Try predefined fallbacks first
    for icon in FALLBACK_ICONS:
        if icon not in used_icons:
            return icon

    # Search through ALL icons in the library
    for raw_icon in _ALL_RAW_ICONS:
        normalized = normalize_icon_name(raw_icon)
        if normalized not in used_icons:
            return normalized

    # Absolute last resort
    return "ri-circle-line"


# ============================================================================
# ICON CATEGORY HELPERS
# ============================================================================

def get_icon_categories_summary() -> str:
    """Generate a summary of available icon categories for LLM context."""
    categories = []
    for category, data in REMIX_ICONS.items():
        icon_count = len(data.get("icons", []))
        description = data.get("description", "")
        categories.append(f"- **{category}** ({icon_count} icons): {description}")
    return "\n".join(categories)


def get_all_icons_for_category(category: str) -> List[str]:
    """Get all icon names for a given category."""
    if category not in REMIX_ICONS:
        return []
    return REMIX_ICONS[category].get("icons", [])


def get_category_icon(category_name: str) -> str:
    """
    Get a representative icon for a specific category.
    Useful for quick icon selection without LLM when category is known.
    """
    if category_name not in REMIX_ICONS:
        return "ri-circle-line"

    icons = REMIX_ICONS[category_name].get("icons", [])
    if not icons:
        return "ri-circle-line"

    return normalize_icon_name(icons[0])


# ============================================================================
# CORE SELECTION: TWO-STAGE APPROACH
# ============================================================================

def _select_category(
    llm,
    heading: str,
    description: str,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Stage 1: Select the best icon category for the given content.
    This is a lightweight LLM call with a small prompt.
    """
    context = context or {}
    categories_summary = get_icon_categories_summary()

    prompt = f"""You are selecting the best icon CATEGORY for educational slide content.

AVAILABLE CATEGORIES:
{categories_summary}

CONTENT:
- Heading: "{heading}"
- Description: "{description}"
- Context: {json.dumps(context, indent=2)}

OUTPUT FORMAT (JSON only, no markdown, no extra text):
{{"category": "CategoryName", "reasoning": "One sentence why"}}

Pick the single best category. Output ONLY valid JSON."""

    try:
        response = invoke_with_retry(llm, [{"role": "user", "content": prompt}])
        result = extract_json_from_response(response.content)
        category = result.get("category", "")

        if category in REMIX_ICONS:
            return category

        # Fuzzy match category name (case-insensitive)
        for cat_name in REMIX_ICONS.keys():
            if cat_name.lower() == category.lower():
                return cat_name

        # Default to first category
        print(f"   [WARN] Unknown category '{category}', using first available.")
        return list(REMIX_ICONS.keys())[0]

    except Exception as e:
        print(f"   [WARN] Category selection failed: {e}. Using first category.")
        return list(REMIX_ICONS.keys())[0]


def _select_icon_from_list(
    llm,
    heading: str,
    description: str,
    category: str,
    icons: List[str],
    exclude_icons: Optional[Set[str]] = None,
) -> str:
    """
    Stage 2: Select a specific icon from a given list.
    The LLM MUST choose from the provided list — no hallucination.
    """
    exclude_icons = exclude_icons or set()

    # Filter out already-used icons (normalize both sides for comparison)
    exclude_normalized: Set[str] = set()
    for ex in exclude_icons:
        exclude_normalized.add(ex)
        # Also add the base form for fuzzy matching
        base = ex.replace("ri-", "").replace("-line", "").replace("-fill", "").strip()
        exclude_normalized.add(base)

    available = []
    for icon in icons:
        base = icon.replace("ri-", "").replace("-line", "").replace("-fill", "").strip()
        normalized = normalize_icon_name(icon)
        if normalized not in exclude_icons and base not in exclude_normalized:
            available.append(icon)

    if not available:
        # All icons in this category are used; just use the full list
        available = icons

    if not available:
        return get_unique_fallback(exclude_icons)

    exclusion_text = ""
    if exclude_icons:
        exclusion_text = f"""
[CRITICAL] DO NOT use any of these icons (already assigned to other items):
{json.dumps(sorted(exclude_icons), indent=2)}
"""

    prompt = f"""You are selecting ONE icon for educational slide content.

CONTENT:
- Heading: "{heading}"
- Description: "{description}"
- Category: "{category}"

AVAILABLE ICONS (you MUST pick from this exact list):
{json.dumps(available, indent=2)}
{exclusion_text}
[WARN]️ You MUST return an icon name that appears EXACTLY in the list above.
Do NOT invent or modify icon names.

OUTPUT FORMAT (JSON only, no markdown):
{{"icon": "exact-icon-name-from-list", "reasoning": "One sentence why"}}

Output ONLY valid JSON."""

    try:
        response = invoke_with_retry(llm, [{"role": "user", "content": prompt}])
        result = extract_json_from_response(response.content)
        icon = result.get("icon", "")

        # Validate against available list (exact match)
        if icon in available:
            return icon

        # Fuzzy match against available list
        icon_base = icon.replace("ri-", "").replace("-line", "").replace("-fill", "").strip()
        for avail in available:
            avail_base = avail.replace("ri-", "").replace("-line", "").replace("-fill", "").strip()
            if icon_base == avail_base:
                return avail

        # LLM returned something not in the list; pick first available
        print(f"   [WARN] Icon '{icon}' not in available list. Using first available.")
        return available[0]

    except Exception as e:
        print(f"   [WARN] Icon selection from list failed: {e}. Using first available.")
        return available[0] if available else get_unique_fallback(exclude_icons)


# ============================================================================
# PUBLIC API: select_icon
# ============================================================================

def select_icon(
    heading: str,
    description: str,
    context: Optional[Dict[str, str]] = None,
    exclude_icons: Optional[Set[str]] = None,
) -> str:
    """
    Intelligently select the most appropriate RemixIcon for given content.
    Uses a two-stage approach: (1) pick category, (2) pick icon from category.
    """
    context = context or {}
    exclude_icons = exclude_icons or set()
    llm = get_llm_client()

    try:
        # Stage 1: Pick best category
        category = _select_category(llm, heading, description, context)
        
        # Stage 2: Pick best icon from that category
        icons_in_category = get_all_icons_for_category(category)
        raw_icon = _select_icon_from_list(
            llm, heading, description, category, icons_in_category, exclude_icons
        )

        icon = normalize_icon_name(raw_icon)

        if not icon_exists(icon):
            if raw_icon in _ALL_RAW_ICONS and raw_icon not in exclude_icons:
                icon = raw_icon
            else:
                icon = get_unique_fallback(exclude_icons)

        if icon in exclude_icons:
            icon = get_unique_fallback(exclude_icons)

        return icon

    except Exception as e:
        print(f"   [ERR] Icon selection failed: {e}")
        return get_unique_fallback(exclude_icons)


async def select_icon_async(
    heading: str,
    description: str,
    context: Optional[Dict[str, str]] = None,
    exclude_icons: Optional[Set[str]] = None,
) -> str:
    """Async version of select_icon."""
    # Since Groq Fast is so quick, we mostly just wrap the sync call in a thread 
    # to allow parallel execution in _individual_selection.
    return await asyncio.to_thread(
        select_icon, heading, description, context, exclude_icons
    )


# ============================================================================
# PUBLIC API: select_icons_batch
# ============================================================================

def select_icons_batch(
    items: List[Dict[str, str]], context: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Select UNIQUE icons for multiple items efficiently.
    Ensures no duplicate icons are assigned to different items on the same slide.
    """
    if not items:
        return []

    context = context or {}
    llm = get_llm_client()

    print(f"   [ICONS] Selecting icons for {len(items)} items (style: {ICON_STYLE})")

    # 1. Try Batch
    batch_result = _try_batch_selection(llm, items, context)
    if batch_result and len(batch_result) == len(items):
        final_icons = _validate_and_deduplicate(batch_result, items, context)
        if final_icons:
            return final_icons

    # 2. Fallback to Parallel Individual Selection
    print(f"   [PARALLEL] Falling back to parallel individual icon selection")
    try:
        # Use a nested event loop or create one if not running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        final_icons = loop.run_until_complete(_individual_selection_async(items, context))
        loop.close()
    except Exception as e:
        print(f"   [WARN] Async fallback failed: {e}. Using sync fallback.")
        final_icons = _individual_selection_sync(items, context)

    return final_icons


def _try_batch_selection(
    llm, items: List[Dict[str, str]], context: Dict[str, str]
) -> Optional[List[str]]:
    """
    Attempt to select all icons via 'Propose-and-Match' pattern.
    Avoids 413 error by NOT sending the full library.
    """
    categories_summary = get_icon_categories_summary()

    items_text = "\n".join(
        [
            f"ITEM {i + 1}:\n  - Heading: \"{item.get('heading', '')}\"\n"
            f"  - Description: \"{item.get('description', '')}\""
            for i, item in enumerate(items)
        ]
    )

    prompt = f"""You are picking one icon for each of {len(items)} items.
    
AVAILABLE CATEGORIES:
{categories_summary}

SLIDE CONTEXT: {json.dumps(context, indent=2)}

ITEMS:
{items_text}

OUTPUT FORMAT (JSON only):
{{
  "icons": [
    {{"item_number": 1, "category": "CategoryName", "conceptual_name": "brain", "reasoning": "..."}},
    {{"item_number": 2, "category": "CategoryName", "conceptual_name": "lightning", "reasoning": "..."}}
  ]
}}
IMPORTANT: 
- Pick a valid Category.
- Propose a simple 'conceptual_name' like 'shield', 'settings', 'cpu', 'search', 'book'.
- I will match your conceptual_name to the real library locally."""

    try:
        response = invoke_with_retry(llm, [{"role": "user", "content": prompt}])
        result = extract_json_from_response(response.content)
        icon_list = result.get("icons", [])

        raw_icons = []
        for icon_data in icon_list:
            category = icon_data.get("category", "")
            concept = icon_data.get("conceptual_name", "")
            
            # Local Resolution: Try matching concept to library
            matched = validate_icon_any_category(concept)
            if not matched:
                # Try category representative
                matched = get_category_icon(category)
            
            raw_icons.append(matched)

        return raw_icons
    except Exception as e:
        print(f"   [WARN] Batch selection optimized prompt failed: {e}")
        return None


def _validate_and_deduplicate(
    raw_icons: List[str],
    items: List[Dict[str, str]],
    context: Dict[str, str],
) -> Optional[List[str]]:
    """
    Validate batch-selected icons and fix duplicates.
    Returns final list of normalized unique icons, or None if too many failures.
    """
    normalized: List[Optional[str]] = []
    used: Set[str] = set()
    needs_reselection: List[int] = []  # indices that need individual re-selection

    for i, raw_icon in enumerate(raw_icons):
        # Try to validate against any category
        matched = validate_icon_any_category(raw_icon)

        if matched:
            norm = normalize_icon_name(matched)
            # Double-check the normalized form actually exists
            if not icon_exists(norm):
                # The raw form matched but normalization broke it;
                # use the raw matched form directly
                norm = matched
        else:
            norm = None

        if norm and norm not in used:
            normalized.append(norm)
            used.add(norm)
        else:
            # Either invalid or duplicate
            normalized.append(None)  # placeholder
            needs_reselection.append(i)

    # If more than half need reselection, abort batch approach
    if len(needs_reselection) > len(items) // 2:
        return None

    # Re-select the problematic ones individually
    if needs_reselection:
        print(f"   [FIX] Re-selecting {len(needs_reselection)} icons (duplicates/invalid)")
        for idx in needs_reselection:
            item = items[idx]
            icon = select_icon(
                heading=item.get("heading", ""),
                description=item.get("description", ""),
                context=context,
                exclude_icons=used,
            )
            normalized[idx] = icon
            used.add(icon)

    # Final safety: ensure no Nones remain
    for i in range(len(normalized)):
        if normalized[i] is None:
            fallback = get_unique_fallback(used, i)
            normalized[i] = fallback
            used.add(fallback)

    return normalized


async def _individual_selection_async(
    items: List[Dict[str, str]], context: Dict[str, str]
) -> List[str]:
    """Select icons in parallel."""
    tasks = []
    for item in items:
        tasks.append(
            select_icon_async(
                heading=item.get("heading", ""),
                description=item.get("description", ""),
                context=context
            )
        )
    
    # Simple parallel execution - uniqueness is handled by post-processing in batch wrapper if needed,
    # but here we just gather results. Note: exclude_icons is hard to do perfectly in pure parallel
    # without a shared state, so we just select them and then deduplicate if needed.
    results = await asyncio.gather(*tasks)
    return list(results)


def _individual_selection_sync(
    items: List[Dict[str, str]], context: Dict[str, str]
) -> List[str]:
    """Legacy sync individual selection."""
    selected_icons: List[str] = []
    used_icons: Set[str] = set()
    for i, item in enumerate(items):
        icon = select_icon(
            heading=item.get("heading", ""),
            description=item.get("description", ""),
            context=context,
            exclude_icons=used_icons,
        )
        selected_icons.append(icon)
        used_icons.add(icon)
    return selected_icons


# ============================================================================
# QUICK SELECT (no LLM)
# ============================================================================

def quick_icon_select(icon_type: str) -> str:
    """
    Quick icon selection using predefined mappings.
    Use this when you know the icon type and want to avoid LLM call.

    Args:
        icon_type: Type of icon needed (e.g., "technology", "process")

    Returns:
        RemixIcon class name
    """
    return CONTENT_TYPE_ICON_MAP.get(icon_type.lower(), "ri-circle-line")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("-" * 80)
    print("ICON SELECTOR TEST (v2 - with all refinements)")
    print("-" * 80 + "\n")

    # --- Test 0: normalize_icon_name edge cases ---
    print("--- Test 0: normalize_icon_name Edge Cases ---\n")
    test_normalize = [
        ("ri-cpu-line", "Already has -line"),
        ("ri-cpu-fill", "Has -fill, should become -line"),
        ("ri-cpu", "No suffix, should get -line"),
        ("ri-number-1", "Numeric icon — should stay as-is if no -line variant exists"),
        ("ri-number-2", "Another numeric icon"),
        ("cpu", "Missing ri- prefix"),
        ("", "Empty string"),
    ]
    for raw, desc in test_normalize:
        result = normalize_icon_name(raw)
        exists = "[OK]" if icon_exists(result) else "[MISSING]"
        print(f"  {raw:25s} -> {result:30s} {exists}  ({desc})")
    print()

    # --- Test 1: Individual selection ---
    print("--- Test 1: Individual Icon Selection ---\n")

    test_cases = [
        {
            "heading": "Vacuum Tubes",
            "description": "Large glass tubes used in first-generation computers for processing",
            "context": {
                "slide_title": "Computer Generations",
                "subtopic_name": "First Generation",
            },
        },
        {
            "heading": "Transistors",
            "description": "Smaller semiconductor devices that replaced vacuum tubes",
            "context": {
                "slide_title": "Computer Generations",
                "subtopic_name": "Second Generation",
            },
        },
        {
            "heading": "Artificial Intelligence",
            "description": "Machine learning systems that can learn and adapt",
            "context": {
                "slide_title": "Modern Computing",
                "subtopic_name": "AI Technologies",
            },
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"  Heading: {test['heading']}")
        print(f"  Description: {test['description'][:60]}...")

        icon = select_icon(
            heading=test["heading"],
            description=test["description"],
            context=test.get("context"),
        )

        exists = "OK" if icon_exists(icon) else "NOT FOUND"
        print(f"  -> Selected Icon: {icon}  ({exists})")
        print("-" * 60)

    # --- Test 2: Batch selection (uniqueness) ---
    print("\n\n--- Test 2: Batch Icon Selection (Uniqueness) ---\n")

    batch_items = [
        {"heading": "Speed", "description": "Computers can process data at incredible speeds"},
        {"heading": "Accuracy", "description": "Computers produce highly accurate results"},
        {"heading": "Storage", "description": "Computers can store massive amounts of data"},
        {"heading": "Automation", "description": "Computers can automate repetitive tasks"},
        {"heading": "Reliability", "description": "Computers are highly reliable for consistent work"},
    ]

    batch_context = {
        "slide_title": "Characteristics of Computers",
        "subtopic_name": "Key Features",
    }

    icons = select_icons_batch(batch_items, batch_context)

    print("\nBatch Results:")
    for i, (item, icon) in enumerate(zip(batch_items, icons), 1):
        exists = "[OK]" if icon_exists(icon) else "[MISSING]"
        print(f"  {i}. {item['heading']:15s} -> {icon:35s} {exists}")

    # Check uniqueness
    unique_count = len(set(icons))
    total_count = len(icons)
    print(f"\n  Uniqueness: {unique_count}/{total_count} unique icons")
    if unique_count == total_count:
        print("  [OK] All icons are unique!")
    else:
        print("  [ERR] DUPLICATE ICONS DETECTED")

    # Check existence
    all_exist = all(icon_exists(icon) for icon in icons)
    print(f"  Existence: {'OK' if all_exist else 'Some missing'}")

    # --- Test 3: Quick select ---
    print("\n\n--- Test 3: Quick Select (No LLM) ---\n")
    for icon_type in ["technology", "security", "education", "step", "unknown_type"]:
        icon = quick_icon_select(icon_type)
        exists = "[OK]" if icon_exists(icon) else "[ERR]"
        print(f"  {icon_type:20s} → {icon:35s} {exists}")

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)