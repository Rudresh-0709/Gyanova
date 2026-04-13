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
import threading
from typing import Dict, List, Optional, Set, Tuple
from functools import lru_cache
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from llm.model_loader import load_groq_fast
except ImportError:
    import sys as _sys
    _sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from app.llm.model_loader import load_groq_fast

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
                    f"   ⏳ Rate limited. Waiting {delay:.1f}s before retry "
                    f"{attempt + 2}/{max_retries}..."
                )
                time.sleep(delay)
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
        print(f"   ⚠ Unknown category '{category}', using first available.")
        return list(REMIX_ICONS.keys())[0]

    except Exception as e:
        print(f"   ⚠ Category selection failed: {e}. Using first category.")
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
🚨 DO NOT use any of these icons (already assigned to other items):
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
⚠️ You MUST return an icon name that appears EXACTLY in the list above.
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
        print(f"   ⚠ Icon '{icon}' not in available list. Using first available.")
        return available[0]

    except Exception as e:
        print(f"   ⚠ Icon selection from list failed: {e}. Using first available.")
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

    Args:
        heading: The bullet point heading/title
        description: The bullet point description text
        context: Additional context (slide_title, slide_purpose, subtopic_name)
        exclude_icons: Set of icon names to avoid (for uniqueness)

    Returns:
        Normalized RemixIcon class name (e.g., "ri-cpu-line")
        Guaranteed to exist in the library (or a valid fallback).
    """
    context = context or {}
    exclude_icons = exclude_icons or set()
    llm = get_llm_client()

    try:
        # Stage 1: Pick best category
        category = _select_category(llm, heading, description, context)
        print(f"   📂 Category: {category}")

        # Stage 2: Pick best icon from that category
        icons_in_category = get_all_icons_for_category(category)
        raw_icon = _select_icon_from_list(
            llm, heading, description, category, icons_in_category, exclude_icons
        )

        # Normalize to ensure consistent suffix handling
        icon = normalize_icon_name(raw_icon)

        # ---------------------------------------------------------------
        # FINAL VALIDATION: ensure the normalized icon actually exists
        # in the library. If the LLM hallucinated or normalize produced
        # an invalid name, fall back safely.
        # ---------------------------------------------------------------
        if not icon_exists(icon):
            print(
                f"   ⚠ Normalized icon '{icon}' does not exist in library. "
                f"Raw was '{raw_icon}'. Falling back."
            )
            # Try using the raw icon directly if it exists
            if raw_icon in _ALL_RAW_ICONS and raw_icon not in exclude_icons:
                icon = raw_icon
                print(f"   🔄 Using raw icon instead: {icon}")
            else:
                icon = get_unique_fallback(exclude_icons)
                print(f"   🔄 Using fallback: {icon}")

        # One more check: make sure it's not in the exclude set
        if icon in exclude_icons:
            icon = get_unique_fallback(exclude_icons)
            print(f"   🔄 Icon was excluded, switched to fallback: {icon}")

        print(f"   ✓ Selected icon: {icon} ({category})")
        return icon

    except Exception as e:
        print(f"   ❌ Icon selection failed: {e}")
        return get_unique_fallback(exclude_icons)


# ============================================================================
# PUBLIC API: select_icons_batch
# ============================================================================

def select_icons_batch(
    items: List[Dict[str, str]], context: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Select UNIQUE icons for multiple items efficiently.
    Ensures no duplicate icons are assigned to different items on the same slide.

    Strategy:
    1. First try a single batch LLM call for efficiency.
    2. Validate & deduplicate the results.
    3. For any items that still need icons (invalid or duplicate), use individual calls.

    Args:
        items: List of dicts with 'heading' and 'description' keys
        context: Shared context for all items

    Returns:
        List of unique, normalized, library-validated icon class names
    """
    if not items:
        return []

    context = context or {}
    llm = get_llm_client()

    print(f"   🎨 Selecting icons for {len(items)} items (style: {ICON_STYLE})")

    # ---------------------------------------------------------------
    # STAGE A: Try a single batch LLM call
    # ---------------------------------------------------------------
    batch_result = _try_batch_selection(llm, items, context)

    if batch_result is not None and len(batch_result) == len(items):
        # Validate and deduplicate
        final_icons = _validate_and_deduplicate(batch_result, items, context)
        if final_icons:
            print(f"   ✓ Selected {len(final_icons)} unique icons via batch")
            return final_icons

    # ---------------------------------------------------------------
    # STAGE B: Fallback to individual selection with dedup tracking
    # ---------------------------------------------------------------
    print(f"   🔄 Falling back to individual icon selection")
    final_icons = _individual_selection(items, context)

    print(f"   ✓ Selected {len(final_icons)} unique icons (individual)")
    return final_icons


def _try_batch_selection(
    llm, items: List[Dict[str, str]], context: Dict[str, str]
) -> Optional[List[str]]:
    """
    Attempt to select all icons in a single LLM call.
    Returns list of raw icon names, or None on failure.
    """
    categories_summary = get_icon_categories_summary()

    # Build full icon library reference (all icons per category)
    icon_library = {}
    for category, data in REMIX_ICONS.items():
        icon_library[category] = data.get("icons", [])

    items_text = "\n".join(
        [
            f"ITEM {i + 1}:\n  - Heading: \"{item.get('heading', '')}\"\n"
            f"  - Description: \"{item.get('description', '')}\""
            for i, item in enumerate(items)
        ]
    )

    prompt = f"""You are selecting visually meaningful icons for {len(items)} educational bullet points.

AVAILABLE ICON CATEGORIES:
{categories_summary}

COMPLETE ICON LIBRARY (you MUST pick icons from these lists):
{json.dumps(icon_library, indent=2)}

SLIDE CONTEXT: {json.dumps(context, indent=2)}

ITEMS:
{items_text}

🚨 CRITICAL REQUIREMENTS:
1. Each item MUST have a DIFFERENT icon — NO DUPLICATES
2. You MUST pick icons that appear EXACTLY in the icon library above
3. Do NOT invent icon names

OUTPUT FORMAT (JSON only, no markdown):
{{
  "icons": [
    {{"item_number": 1, "icon": "exact-icon-from-library", "category": "CategoryName", "reasoning": "Brief"}},
    {{"item_number": 2, "icon": "different-icon-from-library", "category": "CategoryName", "reasoning": "Brief"}}
  ]
}}

Output ONLY valid JSON. Every icon MUST be unique and MUST exist in the library."""

    try:
        response = invoke_with_retry(llm, [{"role": "user", "content": prompt}])
        result = extract_json_from_response(response.content)
        icon_list = result.get("icons", [])

        raw_icons = []
        for icon_data in icon_list:
            raw_icons.append(icon_data.get("icon", ""))

        return raw_icons

    except Exception as e:
        print(f"   ⚠ Batch LLM call failed: {e}")
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
        print(f"   🔧 Re-selecting {len(needs_reselection)} icons (duplicates/invalid)")
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


def _individual_selection(
    items: List[Dict[str, str]], context: Dict[str, str]
) -> List[str]:
    """
    Select icons one by one with duplicate tracking.
    Most reliable but uses more API calls.
    """
    selected_icons: List[str] = []
    used_icons: Set[str] = set()

    for i, item in enumerate(items):
        icon = select_icon(
            heading=item.get("heading", ""),
            description=item.get("description", ""),
            context=context,
            exclude_icons=used_icons,
        )

        # select_icon already checks excludes, but belt-and-suspenders
        if icon in used_icons:
            icon = get_unique_fallback(used_icons, i)

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
    print("\n" + "=" * 80)
    print("ICON SELECTOR TEST (v2 — with all refinements)")
    print("=" * 80 + "\n")

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
        exists = "✅" if icon_exists(result) else "❌"
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

        exists = "✅ exists" if icon_exists(icon) else "❌ NOT FOUND"
        print(f"  ➜ Selected Icon: {icon}  ({exists})")
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
        exists = "✅" if icon_exists(icon) else "❌"
        print(f"  {i}. {item['heading']:15s} -> {icon:35s} {exists}")

    # Check uniqueness
    unique_count = len(set(icons))
    total_count = len(icons)
    print(f"\n  Uniqueness: {unique_count}/{total_count} unique icons")
    if unique_count == total_count:
        print("  ✅ All icons are unique!")
    else:
        print("  ❌ DUPLICATE ICONS DETECTED")

    # Check existence
    all_exist = all(icon_exists(icon) for icon in icons)
    print(f"  Existence: {'✅ All exist' if all_exist else '❌ Some missing'}")

    # --- Test 3: Quick select ---
    print("\n\n--- Test 3: Quick Select (No LLM) ---\n")
    for icon_type in ["technology", "security", "education", "step", "unknown_type"]:
        icon = quick_icon_select(icon_type)
        exists = "✅" if icon_exists(icon) else "❌"
        print(f"  {icon_type:20s} → {icon:35s} {exists}")

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)