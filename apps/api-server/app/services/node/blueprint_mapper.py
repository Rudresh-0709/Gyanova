"""
Intelligent Blueprint Mapper with Groq-Based Selection

This node analyzes templates and dynamically selects blueprints using LLM reasoning.
Based on actual blueprint HTML analysis, it defines accurate content requirements.
"""

import json
from typing import Dict, Any, List

try:
    from ..llm.model_loader import load_groq_fast
except ImportError:
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_groq_fast


# ═══════════════════════════════════════════════════════════════════════════
# BLUEPRINT REGISTRY (Based on actual HTML analysis)
# ═══════════════════════════════════════════════════════════════════════════

BLUEPRINT_CATALOG = {
    "title_card/default.html": {
        "template_matches": ["Title card"],
        "content_type": "NO_NARRATION_POINTS",  # Pure visual slide
        "visual_elements": {
            "heading_badge": "Required (e.g., 'Chapter 1')",
            "main_title": "1-2 lines, 5-8 words total",
            "subtitle": "1-2 sentences, 20-40 words",
            "hero_image": "Required, right-side placement",
        },
        "narration_spec": {
            "format": "paragraph",
            "sentence_count": [3, 5],
            "style": "motivational_hook",
            "note": "Narration is SEPARATE from visual content - just spoken introduction",
        },
    },
    "title_with_bullets/default.html": {
        "template_matches": ["Title with bullets", "Large bullet list"],
        "content_type": "BULLET_POINTS",
        "supports_dynamic_count": True,
        "capacity_ranges": {
            "1-3_items": "Large cards, 1 row",
            "4_items": "2x2 grid",
            "5_items": "2-1-2 staggered",
            "6_items": "3x2 grid",
            "7-9_items": "3x3 grid (compact)",
            "10-12_items": "4x3 grid (very compact)",
        },
        "visual_elements": {
            "main_title": "Required, scalable font",
            "subtitle": "Optional",
            "bullet_cards": {
                "icon": "Required for each",
                "heading": "Bold, 3-6 words",
                "text": "1-2 sentences per bullet",
            },
        },
        "narration_spec": {
            "format": "points",
            "point_count": [2, 6],  # Pedagogically optimal
            "recommended_range": [4, 6],
            "style": "explanatory",
            "structure": "Each narration point = one bullet to generate",
        },
    },
    "title_with_bullets/blob_style.html": {
        "template_matches": ["Title with bullets"],
        "content_type": "BULLET_POINTS",
        "supports_dynamic_count": True,
        "visual_style": "Organic blob shapes",
        "capacity_ranges": {
            "1-3_items": "Large blobs, single row",
            "4-5_items": "Medium blobs, 2x2 or staggered",
            "6-9_items": "Compact blobs, 3x2 or 3x3",
            "10-12_items": "Tiny blobs, 4x3",
        },
        "visual_elements": {
            "main_title": "Centered, prominent",
            "subtitle": "Centered, below title",
            "blob_cards": {
                "icon": "Top-left position, dark bg",
                "heading": "Bold heading",
                "text": "Description text",
            },
        },
        "narration_spec": {
            "format": "points",
            "point_count": [2, 6],  # Pedagogically optimal
            "recommended_range": [3, 6],
            "style": "friendly_explanatory",
            "structure": "Each point becomes one blob",
        },
    },
    "title_with_bullets_and_image/image_left.html": {
        "template_matches": ["Title with bullets and image", "Image and text"],
        "content_type": "BULLET_POINTS",
        "visual_elements": {
            "main_title": "Required",
            "image": "Left side, 40-50% width",
            "bullet_cards": {"count": [3, 4], "format": "Icon + heading + text"},
        },
        "narration_spec": {
            "format": "points",
            "point_count": [3, 4],
            "style": "visual_reference",
            "note": "Fewer points due to image taking space",
        },
    },
    "title_with_bullets_and_image/image_right.html": {
        "template_matches": ["Title with bullets and image", "Text and image"],
        "content_type": "BULLET_POINTS",
        "visual_elements": {
            "main_title": "Required",
            "bullet_cards": {"position": "Left side", "count": [3, 4]},
            "image": "Right side, 40-50% width",
        },
        "narration_spec": {
            "format": "points",
            "point_count": [3, 4],
            "style": "formal_explanatory",
        },
    },
    "cards_and_toggles/icons_with_text.html": {
        "template_matches": ["Icons with text"],
        "content_type": "ICON_GRID",
        "visual_elements": {
            "main_title": "Centered, large",
            "subtitle": "Centered, below accent line",
            "icon_items": {
                "count": [3, 6],
                "layout": "3 cols (3 items), 2x2 (4), 3-2 (5), 3x2 (6)",
                "per_item": {
                    "icon": "Circular, floating",
                    "heading": "Bold, 3-5 words",
                    "text": "1-2 sentences, 12-20 words",
                },
            },
        },
        "narration_spec": {
            "format": "points",
            "point_count": [3, 6],
            "style": "key_takeaways",
            "structure": "Brief statement per icon",
        },
    },
    "cards_and_toggles/toggles.html": {
        "template_matches": ["3 toggles"],
        "content_type": "TOGGLE_CARDS",
        "visual_elements": {
            "toggles": {
                "count": 3,
                "per_toggle": {
                    "question_title": "Compelling question, 8-12 words",
                    "hidden_content": "Detailed answer, 40-60 words",
                },
            }
        },
        "narration_spec": {
            "format": "exploratory_points",
            "point_count": 3,
            "style": "question_answer",
            "structure": "Introduce each question",
        },
    },
    "cards_and_toggles/nested_cards.html": {
        "template_matches": ["3 nested cards"],
        "content_type": "NESTED_CARDS",
        "visual_elements": {
            "cards": {
                "count": 3,
                "levels": ["beginner", "intermediate", "advanced"],
                "per_card": {"title": "Level name", "bullets": "3 points per card"},
            }
        },
        "narration_spec": {
            "format": "layered_points",
            "point_count": 3,
            "style": "progressive_depth",
        },
    },
    "timeline/default.html": {
        "template_matches": ["Timeline"],
        "content_type": "TIMELINE_STEPS",
        "visual_elements": {
            "main_title": "Left-aligned, medium size",
            "timeline_items": {
                "count": [2, 4],  # Responsive: 2 (spacious), 3 (balanced), 4 (compact)
                "per_item": {
                    "dot": "Circle on left line",
                    "phase_title": "Bold heading",
                    "description": "Paragraph text, variable length based on count",
                },
            },
        },
        "narration_spec": {
            "format": "sequential_points",
            "point_count": [2, 4],
            "style": "chronological",
            "structure": "One narration point per timeline step",
        },
    },
    "columns/two_columns.html": {
        "template_matches": ["Two columns"],
        "content_type": "TWO_COLUMN_TEXT",
        "visual_elements": {
            "main_title": "Top of slide",
            "columns": {
                "count": 2,
                "per_column": {
                    "column_title": "Bold heading with underline",
                    "text": "Paragraph format, ~60-100 words",
                },
            },
        },
        "narration_spec": {
            "format": "comparative_points",
            "point_count": [2, 4],  # Can be 1-2 points per column
            "style": "contrasting",
            "structure": "Balanced comparison between sides",
        },
    },
    "columns/three_columns.html": {
        "template_matches": ["Three columns"],
        "content_type": "THREE_COLUMN_CARDS",
        "visual_elements": {
            "columns": {
                "count": 3,
                "per_column": {
                    "icon_or_number": "Optional",
                    "column_title": "3-4 words",
                    "description": "20-30 words",
                },
            }
        },
        "narration_spec": {
            "format": "points",
            "point_count": 3,
            "style": "categorical",
            "structure": "One point per column",
        },
    },
    "columns/four_columns.html": {
        "template_matches": ["Four columns"],
        "content_type": "FOUR_COLUMN_CARDS",
        "visual_elements": {
            "columns": {
                "count": 4,
                "per_column": {
                    "icon": "Required",
                    "title": "2-3 words",
                    "description": "12-18 words (concise)",
                },
            }
        },
        "narration_spec": {
            "format": "points",
            "point_count": 4,
            "style": "concise_categorical",
            "structure": "Brief point per column",
        },
    },
    "diagrams/arrows.html": {
        "template_matches": ["Arrows"],
        "content_type": "FLOW_DIAGRAM",
        "visual_elements": {
            "flow_stages": {
                "count": [3, 4],
                "per_stage": {
                    "stage_title": "4 words max",
                    "details": "2 bullets, 10-15 words each",
                },
            }
        },
        "narration_spec": {
            "format": "sequential_points",
            "point_count": [3, 4],
            "style": "process_flow",
            "structure": "Explain flow logic",
        },
    },
    "diagrams/bargraph.html": {
        "template_matches": ["Column chart", "Line chart", "Diagram"],
        "content_type": "CHART_WITH_ANALYSIS",
        "visual_elements": {
            "chart": "Main visual element",
            "sidebar_analysis": "Text area, 40-60 words",
        },
        "narration_spec": {
            "format": "data_interpretation",
            "sentence_count": [3, 5],
            "style": "analytical",
            "focus": "Trends and insights",
        },
    },
    "charts/column_chart.html": {
        "template_matches": ["Column chart"],
        "content_type": "CHART_WITH_PARAGRAPH",
        "narration_spec": {
            "format": "interpretive",
            "sentence_count": [3, 5],
            "style": "analytical",
        },
    },
    "charts/line_chart.html": {
        "template_matches": ["Line chart"],
        "content_type": "CHART_WITH_BULLETS",
        "narration_spec": {
            "format": "points",
            "point_count": 3,
            "style": "trend_analysis",
        },
    },
    "charts/pie_chart.html": {
        "template_matches": ["Pie chart"],
        "content_type": "CHART_WITH_LEGEND",
        "narration_spec": {
            "format": "proportional",
            "sentence_count": [3, 4],
            "style": "comparative_proportions",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# IMAGE GENERATOR SELECTION LOGIC
# ═══════════════════════════════════════════════════════════════════════════

IMAGE_GENERATOR_CRITERIA = {
    "gemini": {
        "when_to_use": [
            "Historical figures, events, or specific time periods",
            "Specific technical objects (computers, machines, devices)",
            "Architectural landmarks or famous places",
            "Scientific diagrams with precision requirements",
            "Cultural artifacts or specific artworks",
            "Anatomical accuracy needed",
            "Geographic locations or maps",
        ],
        "accuracy_level": "HIGH",
        "cost": "HIGH",
        "speed": "MEDIUM",
    },
    "dalle": {
        "when_to_use": [
            "Abstract concepts and metaphors",
            "Generic icons and symbols",
            "Decorative/thematic backgrounds",
            "Simple illustrations",
            "Conceptual visualizations",
            "Generic people or scenarios",
        ],
        "accuracy_level": "MEDIUM",
        "cost": "MEDIUM",
        "speed": "MEDIUM",
    },
    "flux": {
        "when_to_use": [
            "Quick placeholder images",
            "Simple geometric shapes",
            "Basic backgrounds",
            "Generic patterns",
        ],
        "accuracy_level": "LOW",
        "cost": "LOW",
        "speed": "FAST",
    },
}


def determine_image_generator(
    slide_title: str, slide_purpose: str, subtopic_name: str
) -> Dict[str, Any]:
    """
    Uses LLM to intelligently determine which image generator to use based on accuracy needs.

    Returns:
        {
            "generator": "gemini" | "dalle" | "flux",
            "reasoning": "Why this generator was chosen",
            "image_count": int,
            "image_requirements": [array of image specs]
        }
    """
    llm = load_groq_fast()

    PROMPT = f"""
    Analyze this slide and determine the BEST image generator to use.
    
    SLIDE CONTEXT:
    - Slide Title: {slide_title}
    - Slide Purpose: {slide_purpose}
    - Subtopic: {subtopic_name}
    
    IMAGE GENERATOR OPTIONS:
    {json.dumps(IMAGE_GENERATOR_CRITERIA, indent=2)}
    
    DECISION CRITERIA:
    
    🎯 USE GEMINI (High Accuracy) when:
    - Topic requires SPECIFIC historical accuracy (e.g., "Computer Generations" needs real vacuum tubes, transistors)
    - Depicting real people, places, or time periods
    - Technical precision is critical (e.g., anatomical diagrams, architectural designs)
    - Cultural or geographical specificity needed
    
    🎨 USE DALLE (Medium Accuracy) when:
    - Topic is abstract or conceptual (e.g., "Features of AI", "Benefits of Cloud")
    - Generic visual metaphors work (e.g., lightbulb for "ideas", cloud for "storage")
    - Illustrative rather than documentary
    
    ⚡ USE FLUX (Low Accuracy, Fast) when:
    - Simple decorative backgrounds
    - Generic shapes or patterns
    - Quick placeholder visuals
    
    RESPOND WITH JSON ONLY:
    {{
      "generator": "gemini" | "dalle" | "flux",
      "reasoning": "1-2 sentences explaining why this generator is best",
      "requires_high_accuracy": true/false,
      "example_prompts": ["Example prompt 1", "Example prompt 2"]
    }}
    """

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        # Validate generator choice
        if result.get("generator") in IMAGE_GENERATOR_CRITERIA:
            return {
                "image_generator": result["generator"],
                "generator_reasoning": result.get("reasoning", ""),
                "requires_high_accuracy": result.get("requires_high_accuracy", False),
                "example_prompts": result.get("example_prompts", []),
            }
    except Exception as e:
        print(f"⚠ Image generator selection failed: {e}, defaulting to DALLE")

    # Fallback to DALLE (balanced choice)
    return {
        "image_generator": "dalle",
        "generator_reasoning": "Default choice - balanced accuracy and cost",
        "requires_high_accuracy": False,
        "example_prompts": [],
    }


def select_blueprint_with_groq(
    template_name: str, slide_context: Dict[str, Any]
) -> str:
    """Uses Groq LLM to intelligently select the best blueprint for a template."""
    llm = load_groq_fast()

    # Find matching blueprints
    matching_blueprints = []
    for blueprint_path, spec in BLUEPRINT_CATALOG.items():
        if template_name in spec.get("template_matches", []):
            matching_blueprints.append(
                {
                    "path": blueprint_path,
                    "content_type": spec.get("content_type"),
                    "visual_style": spec.get("visual_style", "default"),
                    "capacity": spec.get(
                        "capacity_ranges", spec.get("visual_elements")
                    ),
                }
            )

    if not matching_blueprints:
        return "title_with_bullets/default.html"  # Fallback

    if len(matching_blueprints) == 1:
        return matching_blueprints[0]["path"]

    # Use LLM to choose between multiple options
    slide_title = slide_context.get("slide_title", "")
    slide_purpose = slide_context.get("slide_purpose", "")
    narration_role = slide_context.get("narration_role", "")

    PROMPT = f"""
    Choose the BEST blueprint for this slide from the options below.
    
    SLIDE CONTEXT:
    - Title: {slide_title}
    - Purpose: {slide_purpose}
    - Narration Role: {narration_role}
    - Template: {template_name}
    
    AVAILABLE BLUEPRINTS:
    {json.dumps(matching_blueprints, indent=2)}
    
    SELECTION CRITERIA:
    - Choose "default" for standard, professional look
    - Choose "blob_style" for friendly, modern, organic feel
    - Choose "image_left" if visual should come first
    - Choose "image_right" if text explanation should come first
    
    RESPOND WITH JSON ONLY:
    {{
      "selected_path": "exact blueprint path from options",
      "reasoning": "1 sentence why"
    }}
    """

    try:
        response = llm.invoke([{"role": "user", "content": PROMPT}])
        content = response.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        selected = result.get("selected_path")

        # Validate selection
        if selected and any(bp["path"] == selected for bp in matching_blueprints):
            return selected
    except:
        pass

    # Fallback to first match
    return matching_blueprints[0]["path"]


def blueprint_mapper_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligently maps templates to blueprints and enriches with accurate constraints.
    Also determines which image generator to use for slides with images.
    """
    slide_plan = state.get("slide_plan", {})

    for sub_id, sub_data in slide_plan.items():
        slides = sub_data.get("slides", [])
        subtopic_name = sub_data.get("subtopic_name", "")

        for slide in slides:
            template = slide.get("selected_template")

            # Use Groq to select the best blueprint
            blueprint_path = select_blueprint_with_groq(template, slide)

            if blueprint_path in BLUEPRINT_CATALOG:
                spec = BLUEPRINT_CATALOG[blueprint_path]

                # Add blueprint metadata
                slide["blueprint_file"] = blueprint_path
                slide["content_type"] = spec.get("content_type")
                slide["visual_elements"] = spec.get("visual_elements", {})

                # Add narration constraints
                narration_spec = spec.get("narration_spec", {})
                slide["narration_format"] = narration_spec.get("format", "points")
                slide["narration_constraints"] = {
                    "point_count": narration_spec.get("point_count"),
                    "sentence_count": narration_spec.get("sentence_count"),
                    "style": narration_spec.get("style", ""),
                    "structure": narration_spec.get("structure", ""),
                    "note": narration_spec.get("note", ""),
                }

                # ⭐ NEW: Determine image generator if blueprint uses images
                content_type = spec.get("content_type", "")
                requires_image = any(
                    [
                        "image" in blueprint_path.lower(),
                        content_type
                        in ["NO_NARRATION_POINTS"],  # Title cards have hero images
                        "chart" in blueprint_path.lower(),
                    ]
                )

                if requires_image:
                    image_decision = determine_image_generator(
                        slide_title=slide.get("slide_title", ""),
                        slide_purpose=slide.get("slide_purpose", ""),
                        subtopic_name=subtopic_name,
                    )
                    slide["image_generator"] = image_decision["image_generator"]
                    slide["image_generator_reasoning"] = image_decision[
                        "generator_reasoning"
                    ]
                    slide["requires_high_accuracy"] = image_decision[
                        "requires_high_accuracy"
                    ]

                    print(
                        f"✓ Mapped '{slide.get('slide_title')}' → {blueprint_path} [IMG: {image_decision['image_generator'].upper()}]"
                    )
                else:
                    print(f"✓ Mapped '{slide.get('slide_title')}' → {blueprint_path}")
            else:
                print(f"⚠ No blueprint found for template '{template}', using fallback")
                slide["blueprint_file"] = "title_with_bullets/default.html"
                slide["narration_format"] = "points"
                slide["narration_constraints"] = {"point_count": [4, 6]}

    state["slide_plan"] = slide_plan
    return state


if __name__ == "__main__":
    test_state = {
        "slide_plan": {
            "sub_1_2b67b6": {
                "subtopic_name": "Introduction to Computer Generations",
                "slides": [
                    {
                        "slide_title": "Introduction to Computer Generations",
                        "slide_purpose": "definition",
                        "selected_template": "Title card",
                        "narration_role": "Introduce",
                        "narration_goal": "Learners should understand what computer generations are and why studying them is important for grasping computing evolution.",
                        "reasoning": "A Title card is ideal for starting the lesson with a clear, impactful title and a brief hook to engage beginners.",
                        "slide_id": "sub_1_2b67b6_s1",
                    },
                    {
                        "slide_title": "Overview of Computer Generations",
                        "slide_purpose": "intuition",
                        "selected_template": "Timeline",
                        "narration_role": "Guide",
                        "narration_goal": "Learners should gain an intuitive understanding of the chronological progression and key milestones of each computer generation.",
                        "reasoning": "A Timeline template effectively presents historical progression, helping beginners visualize the evolution over time.",
                        "slide_id": "sub_1_2b67b6_s2",
                    },
                    {
                        "slide_title": "Key Features of Each Generation",
                        "slide_purpose": "reinforcement",
                        "selected_template": "Four columns",
                        "narration_role": "Reinforce",
                        "narration_goal": "Learners should be able to recall the main characteristics and technological advances of the first four computer generations.",
                        "reasoning": "Four columns allow concise, side-by-side comparison of features for each generation, reinforcing learning with clear structure.",
                        "slide_id": "sub_1_2b67b6_s3",
                    },
                ],
            }
        }
    }

    result = blueprint_mapper_node(test_state)

    print("\n" + "=" * 80)
    print("BLUEPRINT MAPPING RESULTS - Computer Generations")
    print("=" * 80 + "\n")

    for slide in result["slide_plan"]["sub_1_2b67b6"]["slides"]:
        print(f"📄 {slide['slide_title']}")
        print(f"   Template: {slide['selected_template']}")
        print(f"   Blueprint: {slide.get('blueprint_file', 'N/A')}")
        print(f"   Content Type: {slide.get('content_type', 'N/A')}")
        print(f"   Narration Format: {slide.get('narration_format', 'N/A')}")

        constraints = slide.get("narration_constraints", {})
        if constraints.get("point_count"):
            print(f"   Point Count: {constraints['point_count']}")
        elif constraints.get("sentence_count"):
            print(f"   Sentence Count: {constraints['sentence_count']}")

        if constraints.get("style"):
            print(f"   Style: {constraints['style']}")

        print()

    print("=" * 80)
    templates_used = [
        s["selected_template"] for s in result["slide_plan"]["sub_1_2b67b6"]["slides"]
    ]
    print(
        f"✅ Template Diversity: {len(set(templates_used))}/{len(templates_used)} unique"
    )
    print(f"   Templates: {templates_used}")
    print("=" * 80)
