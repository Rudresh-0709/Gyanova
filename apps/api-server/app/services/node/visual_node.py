from ..llm.model_loader import load_groq,load_groq_fast,load_openai
from ..state import TutorState
import ast
import json

# def generate_visuals(state:TutorState)->TutorState:


import random

from typing import Dict, Any

def generate_visual_info(state: TutorState) -> TutorState:
    """
    Iterate through slides and decide the best type of visual for each slide.
    Adds a `visual_info` dict to each slide in state.
    """
    updated_slides = []
    for slide in state.slides:
        hint = slide.get("visual", "").lower()
        key_terms = slide.get("key_terms", [])

        if "timeline" in hint or "evolution" in hint:
            visual_info = {
                "visual_type": "diagram",
                "visual_description": f"Timeline diagram illustrating {hint}",
                "stock_image_suggestion": None,
                "ai_image_prompt": None,
            }
        elif "example" in hint or "real-world" in hint:
            visual_info = {
                "visual_type": "stock_image",
                "visual_description": None,
                "stock_image_suggestion": f"Stock photo related to {', '.join(key_terms)}",
                "ai_image_prompt": None,
            }
        else:
            visual_info = {
                "visual_type": "ai_image",
                "visual_description": None,
                "stock_image_suggestion": None,
                "ai_image_prompt": f"AI illustration of {hint} with focus on {', '.join(key_terms)}",
            }

        # attach visual_info back to slide
        slide["visual_info"] = visual_info
        updated_slides.append(slide)

    state.slides = updated_slides
    return state