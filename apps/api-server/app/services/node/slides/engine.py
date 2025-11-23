# engine.py

from typing import Dict, List, Any
import uuid


def generate_slide_id():
    return f"slide_{uuid.uuid4().hex[:8]}"


def normalize_slide(sub_id: str, slide: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw slide from your state into a unified structured slide dict
    that your frontend can directly render.
    """

    return {
        "id": generate_slide_id(),
        "sub_id": sub_id,
        "title": slide.get("title"),
        "layout": slide.get("design", {}).get("layout_mode", "layout-center"),
        "decoration": slide.get("design", {}).get("decoration_style", None),
        "point_display": slide.get("design", {}).get("point_display", None),

        # core content
        "points": slide.get("points", []),

        # blocks such as timeline, explanation, comparison, statistics, etc.
        "contentBlocks": slide.get("contentBlocks", []),

        # image generation
        "imageType": slide.get("imageType"),
        "imagePrompt": slide.get("imagePrompt"),
        "template": slide.get("template"),

        # frontend assist
        "has_image": slide.get("imageType") is not None,
    }


def generate_slides_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: user state containing topics, subtopics, slides
    Output: fully normalized JSON ready for frontend renderer.
    """

    final_output = {
        "topic": state.get("topic"),
        "sub_topics": state.get("sub_topics"),
        "slides": {}
    }

    slides_dict = state.get("slides", {})

    for sub in state.get("sub_topics", []):
        sub_id = sub["id"]
        raw_slides = slides_dict.get(sub_id, [])

        normalized_list = []
        for slide in raw_slides:
            normalized = normalize_slide(sub_id, slide)
            normalized_list.append(normalized)

        final_output["slides"][sub_id] = normalized_list

    return final_output


# -------------------------------------------------------------------
# Example usage:
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Put your state here for testing
    state = {
        "topic": "Computer generations",
        "sub_topics": [
            {
                "name": "Introduction to Computer Generations",
                "difficulty": "Beginner",
                "id": "sub_1_2b67b6",
            }
        ],
        "slides": {
            "sub_1_2b67b6": [
                {
                    "title": "Evolution of Computers",
                    "points": [
                        "Computers have evolved through distinct generations, each marked by significant advancements.",
                        "First generation computers used vacuum tubes, while second generation computers adopted transistors.",
                        "Third generation computers integrated integrated circuits, leading to smaller, more powerful machines.",
                    ],
                    "template": "image_left",
                    "imageType": "ai_enhanced_image",
                    "imagePrompt": "...",
                    "design": {
                        "layout_mode": "layout-timeline",
                        "decoration_style": "decor-tech",
                        "point_display": "points-list",
                    },
                    "contentBlocks": [
                        {
                            "type": "timeline",
                            "events": [
                                {
                                    "year": "1940s-1950s",
                                    "description": "First Generation...",
                                }
                            ],
                        },
                        {
                            "type": "explanation",
                            "paragraphs": [
                                "Each generation improved hardware...",
                            ],
                        },
                    ],
                }
            ]
        }
    }

    output = generate_slides_from_state(state)
    import json
    print(json.dumps(output, indent=2))
