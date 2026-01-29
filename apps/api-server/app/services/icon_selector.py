"""
Smart Icon Selector - Uses Groq LLM to select contextually appropriate icons

This module provides intelligent icon selection from the RemixIcon library based on:
- Semantic meaning of the content
- Icon category descriptions
- Context (heading, description, slide purpose)

Instead of hardcoding icon names, content generation can request icon TYPES,
and this module will select the most appropriate specific icon.
"""

import os
import sys
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from llm.model_loader import load_groq_fast
except ImportError:
    # Fallback for different directory structure
    import sys as _sys

    _sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from app.llm.model_loader import load_groq_fast

load_dotenv()

# Load RemixIcon library
ICONS_PATH = os.path.join(os.path.dirname(__file__), "remix-icons.json")

with open(ICONS_PATH, "r", encoding="utf-8") as f:
    REMIX_ICONS = json.load(f)


def get_icon_categories_summary() -> str:
    """Generate a summary of available icon categories for LLM context"""
    categories = []
    for category, data in REMIX_ICONS.items():
        icon_count = len(data.get("icons", []))
        description = data.get("description", "")
        categories.append(f"- **{category}** ({icon_count} icons): {description}")

    return "\n".join(categories)


def select_icon(
    heading: str, description: str, context: Optional[Dict[str, str]] = None
) -> str:
    """
    Intelligently select the most appropriate RemixIcon for given content.

    Args:
        heading: The bullet point heading/title
        description: The bullet point description text
        context: Additional context (slide_title, slide_purpose, subtopic_name)

    Returns:
        RemixIcon class name (e.g., "ri-cpu-line")

    Strategy:
    1. Analyze the semantic meaning of the heading and description
    2. Match to the most appropriate icon category
    3. Select specific icon from that category
    """
    llm = load_groq_fast()
    context = context or {}

    # Prepare category information
    categories_summary = get_icon_categories_summary()

    # Get sample icons from each category for better selection
    category_samples = {}
    for category, data in REMIX_ICONS.items():
        icons = data.get("icons", [])
        # Take first 5 icons as samples
        category_samples[category] = icons[:5]

    PROMPT = f"""
You are an expert at selecting visually meaningful icons for educational content.

AVAILABLE ICON CATEGORIES:
{categories_summary}

CONTENT TO ICON:
- Heading: "{heading}"
- Description: "{description}"
- Slide Context: {json.dumps(context, indent=2)}

YOUR TASK:
1. Analyze the semantic meaning of the heading and description
2. Identify which icon CATEGORY best represents this content
3. Select ONE specific icon from that category

SELECTION RULES:
- Choose icons that visually represent the concept clearly
- Prefer simple, recognizable icons over complex ones
- Consider the educational context (teaching, learning, technical concepts)
- Technology/Computing → use "Development", "Devices", or "Design" categories
- Processes/Steps → use "Arrows" or "System" categories  
- Communication → use "Communication" or "Business" categories
- Objects/Things → use relevant category (Buildings, Devices, etc.)

CATEGORY SAMPLES (first 5 icons from each):
{json.dumps(category_samples, indent=2)}

OUTPUT FORMAT (JSON only, no markdown):
{{
  "category": "CategoryName",
  "icon": "ri-icon-name",
  "reasoning": "Brief explanation of why this icon fits"
}}

Choose wisely - the icon must make sense to students seeing it for the first time.
"""

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        selected_icon = result.get("icon", "")
        category = result.get("category", "")

        # Validate that the icon actually exists in the category
        if category in REMIX_ICONS:
            available_icons = REMIX_ICONS[category].get("icons", [])
            if selected_icon in available_icons:
                print(f"   ✓ Selected icon: {selected_icon} ({category})")
                return selected_icon
            else:
                print(f"   ⚠ Icon {selected_icon} not in {category}, using first icon")
                return available_icons[0] if available_icons else "ri-circle-line"
        else:
            print(f"   ⚠ Invalid category {category}, using default")
            return "ri-circle-line"

    except Exception as e:
        print(f"   ❌ Icon selection failed: {e}")
        # Fallback to a safe default
        return "ri-circle-line"


def select_icons_batch(
    items: List[Dict[str, str]], context: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Select icons for multiple items efficiently.

    Args:
        items: List of dicts with 'heading' and 'description' keys
        context: Shared context for all items

    Returns:
        List of icon class names
    """
    icons = []
    for item in items:
        icon = select_icon(
            heading=item.get("heading", ""),
            description=item.get("description", ""),
            context=context,
        )
        icons.append(icon)

    return icons


def get_category_icon(category_name: str) -> str:
    """
    Get a representative icon for a specific category.
    Useful for quick icon selection without LLM when category is known.

    Args:
        category_name: Name of the category (e.g., "Development", "Business")

    Returns:
        A representative icon from that category
    """
    if category_name not in REMIX_ICONS:
        return "ri-circle-line"

    icons = REMIX_ICONS[category_name].get("icons", [])
    if not icons:
        return "ri-circle-line"

    # Return the first icon as a representative
    return icons[0]


# Predefined mappings for common content types (faster than LLM, use as fallback)
CONTENT_TYPE_ICON_MAP = {
    "technology": "ri-cpu-line",
    "process": "ri-arrow-right-circle-line",
    "feature": "ri-star-line",
    "benefit": "ri-checkbox-circle-line",
    "step": "ri-number-1",
    "data": "ri-database-line",
    "network": "ri-network-line",
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


if __name__ == "__main__":
    # Test the icon selector
    print("\n" + "=" * 80)
    print("ICON SELECTOR TEST")
    print("=" * 80 + "\n")

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

        print(f"  Selected Icon: {icon}")
        print("-" * 80)
