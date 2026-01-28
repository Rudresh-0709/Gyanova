import json
import uuid
from typing import Dict, Any, List

try:
    from ..llm.model_loader import load_openai, load_groq
    from ..state import TutorState
except ImportError:
    # Fallback for direct script execution or different import paths
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_openai, load_groq
    from state import TutorState

# TEMPLATE REGISTRY
SLIDE_TEMPLATES = {
    # ─────────────────────────────────────────────────────────────
    # HERO & TITLE SECTION
    # ─────────────────────────────────────────────────────────────
    "Title card": {
        "template_name": "Title card",
        "when_to_use": ["Start of a lesson", "Start of a new chapter or subtopic"],
        "how_to_make": {
            "title": "Clear, high-impact concept name (5-8 words)",
            "subtitle": "2-sentence hook explaining why this matters (20-30 words)",
            "image": "High-quality, thematic background or side hero",
            "layout_note": "Text should take up 40% of screen area visually",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # TEXT & EXPLANATION LAYOUTS
    # ─────────────────────────────────────────────────────────────
    "Title with bullets": {
        "template_name": "Title with bullets",
        "when_to_use": [
            "Explaining a concept in points",
            "Breaking down ideas logically",
        ],
        "how_to_make": {
            "title": "Concept or idea",
            "bullets": "4-5 points total",
            "bullet_format": "Bold Header + 1 sentence explanation per point",
            "density": "Total text should be ~80-100 words to avoid whitespace",
        },
    },
    "Title with bullets and image": {
        "template_name": "Title with bullets and image",
        "when_to_use": [
            "Concept explanation that benefits from visualization",
            "Abstract topics needing visual support",
        ],
        "how_to_make": {
            "title": "Concept name",
            "bullets": "3-4 key ideas",
            "bullet_format": "Each bullet must have a 15-word description",
            "image": "Vertical aspect ratio to match text height",
            "text_balance": "Text column and image column should appear equal height",
        },
    },
    "Image and text": {
        "template_name": "Image and text",
        "when_to_use": ["Building intuition", "Narrative-style teaching"],
        "how_to_make": {
            "image": "Primary visual element (takes 50% width)",
            "text": "1 Headline + 2 substantial paragraphs (approx 60 words each)",
            "tone": "Conversational but detailed",
            "avoid": "Single sentence descriptions",
        },
    },
    "Text and image": {
        "template_name": "Text and image",
        "when_to_use": [
            "Formal explanation first, visual second",
            "Definitions with supporting imagery",
        ],
        "how_to_make": {
            "text": "Structured explanation (Headline + 3-4 detailed points)",
            "image": "Supportive, secondary",
            "content_fill": "Text must physically occupy the same vertical height as the image",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # COLUMNS & COMPARISONS
    # ─────────────────────────────────────────────────────────────
    "Two columns": {
        "template_name": "Two columns",
        "when_to_use": ["Comparisons", "Pros vs cons", "Theory vs example"],
        "how_to_make": {
            "left_column": "Title + 3-4 descriptive points (Bold + Text)",
            "right_column": "Title + 3-4 descriptive points (Bold + Text)",
            "balance": "Both sides must have equal word count (~60 words per side)",
        },
    },
    "Three columns": {
        "template_name": "Three columns",
        "when_to_use": ["Categorization", "Types or classes"],
        "how_to_make": {
            "columns": "Exactly 3",
            "item_format": "Icon + Title + 25-word description per column",
            "avoid": "Orphan titles without descriptions",
        },
    },
    "Four columns": {
        "template_name": "Four columns",
        "when_to_use": ["Lists of components", "Feature breakdowns"],
        "how_to_make": {
            "columns": "Exactly 4",
            "item_format": "Title + 15-word concise explanation per column",
            "icons": "Mandatory to fill vertical space",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # PROCESS & FLOW
    # ─────────────────────────────────────────────────────────────
    "Timeline": {
        "template_name": "Timeline",
        "when_to_use": ["Processes", "Historical progression"],
        "how_to_make": {
            "steps": "4-6 sequential steps",
            "step_content": "Year/Phase + Title + 1 sentence context",
            "visual_fill": "Ensure text alternates or fills the space below/above the line",
        },
    },
    "Arrows": {
        "template_name": "Arrows",
        "when_to_use": ["Cause-effect relationships", "Input → output explanation"],
        "how_to_make": {
            "nodes": "3-4 distinct stages",
            "node_content": "Box containing: Title + 2 bullet points of detail",
            "direction": "Left to right",
            "fill_strategy": "Cards should be wide to fill the slide width",
        },
    },
    "Diagram": {
        "template_name": "Diagram",
        "when_to_use": ["System architecture", "Complex abstractions"],
        "how_to_make": {
            "elements": "Visual diagram in center",
            "sidebar_text": "Mandatory: A 'Key Takeaway' sidebar with ~50 words explaining the diagram",
            "labels": "Detailed labels, not just keywords",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # LISTS & SUMMARIES
    # ─────────────────────────────────────────────────────────────
    "Icons with text": {
        "template_name": "Icons with text",
        "when_to_use": ["Key takeaways", "Concept reinforcement"],
        "how_to_make": {
            "items": "4-6 items",
            "format": "Icon (Left) + Bold Title + 1 sentence description (Right)",
            "layout": "Grid 2x2 or 2x3 to fill screen",
        },
    },
    "Large bullet list": {
        "template_name": "Large bullet list",
        "when_to_use": ["Summaries", "Revision slides"],
        "how_to_make": {
            "bullets": "5-6 points",
            "text": "Full sentences (15-20 words each)",
            "styling": "Large font size, generous line height to fill vertical space",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # INTERACTIVE & PROGRESSIVE
    # ─────────────────────────────────────────────────────────────
    "3 toggles": {
        "template_name": "3 toggles",
        "when_to_use": ["Progressive disclosure", "Deep dive into 3 questions"],
        "how_to_make": {
            "toggle_title": "Compelling question or topic",
            "content": "Hidden explanation must be substantial (40-50 words per toggle)",
            "tone": "Exploratory",
        },
    },
    "3 nested cards": {
        "template_name": "3 nested cards",
        "when_to_use": ["Layered learning", "Beginner → intermediate → advanced"],
        "how_to_make": {
            "cards": "3 distinct layers",
            "content": "Each card must have Title + 3 bullet points of detail",
            "visual": "Cards should overlap but have enough text to look full",
        },
    },
    # ─────────────────────────────────────────────────────────────
    # DATA & CHARTS (Preventing emptiness)
    # ─────────────────────────────────────────────────────────────
    "Column chart": {
        "template_name": "Column chart",
        "when_to_use": ["Comparing quantities"],
        "how_to_make": {
            "data": "Clear values",
            "analysis_text": "Mandatory: A 50-word 'Analysis' paragraph beside the chart explaining the trend",
            "labels": "Descriptive",
        },
    },
    "Line chart": {
        "template_name": "Line chart",
        "when_to_use": ["Trends over time"],
        "how_to_make": {
            "data": "Sequential",
            "analysis_text": "Mandatory: 'Key Observations' list (3 points) beside the chart",
        },
    },
    "Pie chart": {
        "template_name": "Pie chart",
        "when_to_use": ["Proportions"],
        "how_to_make": {
            "segments": "3-6 max",
            "legend": "Detailed legend with descriptions, not just labels",
            "analysis_text": "Summary paragraph (40 words) explaining the largest segment",
        },
    },
}

SLIDE_PURPOSES = [
    "definition",
    "intuition",
    "process",
    "comparison",
    "visualization",
    "reinforcement",
    "assessment",
]
NARRATION_ROLES = [
    "Introduce",
    "Interpret",
    "Guide",
    "Contrast",
    "Emphasize",
    "Connect",
    "Reinforce",
    "Question",
]


def plan_slides_for_subtopic(
    subtopic: Dict[str, Any], teacher_profile: str = "Expert Teacher"
) -> Dict[str, Any]:
    """Calls LLM to plan slides for a single subtopic."""
    llm = load_openai()  # Use OpenAI for complex planning

    subtopic_name = subtopic.get("name")
    difficulty = subtopic.get("difficulty", "Beginner")

    # Determine slide count based on difficulty
    if difficulty.lower() == "beginner":
        min_s, max_s = 2, 4
    elif difficulty.lower() == "intermediate":
        min_s, max_s = 4, 6
    else:
        min_s, max_s = 5, 8

    SYSTEM_PROMPT = f"""
    You are an AI Curriculum Planner. Your goal is to break down a subtopic into a series of educational slides.
    
    CONTEXT:
    - Teacher Profile: {teacher_profile}
    - Subtopic: {subtopic_name}
    - Difficulty: {difficulty}
    
    AVAILABLE TEMPLATES (Choose ONLY from these):
    {json.dumps(SLIDE_TEMPLATES, indent=2)}
    
    SLIDE PURPOSES:
    {json.dumps(SLIDE_PURPOSES)}
    
    NARRATION ROLES:
    {json.dumps(NARRATION_ROLES)}
    
    YOUR RESPONSIBILITIES:
    1. Break the subtopic into {min_s} to {max_s} slides.
    2. For each slide:
        - Choose ONE slide_purpose strictly from the provided SLIDE_PURPOSES list.
        - Choose ONE selected_template strictly from the TEMPLATE KEYS (dictionary keys).
        - Ensure the template logically matches the slide_purpose.
    3. Define a clear Narration Goal (what the learner should understand).
    4. Provide a short reasoning for your choices.

    ⭐ TEMPLATE DIVERSITY RULES (CRITICAL):
    - AVOID REPEATING TEMPLATES unless pedagogically essential
    - If you must repeat a template, there should be a STRONG justification
    - Aim for variety: use different templates for different purposes
    - Example: Don't use "Title with bullets" for all explanations - mix with "Two columns", "Timeline", etc.
    
    ⭐ IMAGE USAGE DECISION CRITERIA:
    When deciding between "Title with bullets" vs "Title with bullets and image":
    - USE IMAGE when:
      * Topic is visual/spatial (e.g., architecture, anatomy, geography)
      * Concept is abstract and benefits from metaphor (e.g., algorithms, data flow)
      * Historical/timeline content with relevant imagery
      * Technical diagrams enhance understanding
    - SKIP IMAGE when:
      * Pure logical/textual concepts (e.g., definitions, procedures)
      * Lists of features, advantages, rules
      * Topic is self-explanatory from text alone
    
    CRITICAL:
        - selected_template MUST be EXACTLY one of the template dictionary keys.
        - slide_purpose MUST be EXACTLY one of the provided slide purposes.
        - Prioritize template DIVERSITY over repetition
    
    OUTPUT RULES:
    - Output ONLY valid JSON in the following format:
    {{
        "slides": [
            {{
                "slide_title": "...",
                "slide_purpose": "...",
                "selected_template": "...",
                "narration_role": "...",
                "narration_goal": "...",
                "reasoning": "..."
            }}
        ]
    }}
    - No narration text or slide content.
    - Logical flow: Start with basics/definitions, move to intuition/examples, and end with reinforcement.
    """

    USER_PROMPT = (
        f"Plan the slides for the subtopic: '{subtopic_name}' at {difficulty} level."
    )

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

    try:
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)

        # ---- VALIDATION STARTS HERE ----
        VALID_TEMPLATES = set(SLIDE_TEMPLATES.keys())
        VALID_PURPOSES = set(SLIDE_PURPOSES)
        VALID_NARRATION = set(NARRATION_ROLES)

        validated_slides = []

        for slide in data.get("slides", []):
            if slide.get("selected_template") not in VALID_TEMPLATES:
                continue
            if slide.get("slide_purpose") not in VALID_PURPOSES:
                continue
            if slide.get("narration_role") not in VALID_NARRATION:
                continue
            if not slide.get("slide_title"):
                continue  # title is mandatory

            validated_slides.append(slide)

        data["slides"] = validated_slides
        # ---- VALIDATION ENDS HERE ----

        return data

    except Exception as e:
        print(f"Error parsing slide plan for {subtopic_name}: {e}")
        return {"slides": []}


def slide_planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node to process all subtopics and build a slide plan."""
    if "slide_plan" not in state or state["slide_plan"] is None:
        state["slide_plan"] = {}

    sub_topics = state.get("sub_topics", [])

    for subtopic in sub_topics:
        sub_id = subtopic.get("id")
        if sub_id not in state["slide_plan"]:
            print(f"Planning slides for: {subtopic.get('name')}...")
            plan_data = plan_slides_for_subtopic(subtopic)

            # Ensure slide_ids are unique
            slides = plan_data.get("slides", [])
            for i, slide in enumerate(slides):
                slide["slide_id"] = f"{sub_id}_s{i+1}"

            state["slide_plan"][sub_id] = {
                "subtopic_name": subtopic.get("name"),
                "slides": slides,
            }

    return state


if __name__ == "__main__":
    State = {
        "topic": "Computer generations",
        "sub_topics": [
            {
                "name": "Introduction to Computer Generations",
                "difficulty": "Beginner",
                "id": "sub_1_2b67b6",
            },
            {
                "name": "First Generation Computers (1940s-1950s): Vacuum Tubes",
                "difficulty": "Intermediate",
                "id": "sub_2_30755b",
            },
            {
                "name": "Second to Fifth Generation Computers (1950s-1980s): Transistors, Integrated Circuits, and Microprocessors",
                "difficulty": "Intermediate",
                "id": "sub_3_d87eaf",
            },
            {
                "name": "Modern Computer Generations (1980s-present): Artificial Intelligence, Internet, and Beyond",
                "difficulty": "Advanced",
                "id": "sub_4_c8e0dd",
            },
            {
                "name": "Comparison and Evolution of Computer Generations",
                "difficulty": "Intermediate",
                "id": "sub_5_dca7e2",
            },
        ],
    }

    result = slide_planning_node(State)
    print(json.dumps(result, indent=2))


{
    "topic": "Computer generations",
    "sub_topics": [
        {
            "name": "Introduction to Computer Generations",
            "difficulty": "Beginner",
            "id": "sub_1_2b67b6",
        },
        {
            "name": "First Generation Computers (1940s-1950s): Vacuum Tubes",
            "difficulty": "Intermediate",
            "id": "sub_2_30755b",
        },
        {
            "name": "Second to Fifth Generation Computers (1950s-1980s): Transistors, Integrated Circuits, and Microprocessors",
            "difficulty": "Intermediate",
            "id": "sub_3_d87eaf",
        },
        {
            "name": "Modern Computer Generations (1980s-present): Artificial Intelligence, Internet, and Beyond",
            "difficulty": "Advanced",
            "id": "sub_4_c8e0dd",
        },
        {
            "name": "Comparison and Evolution of Computer Generations",
            "difficulty": "Intermediate",
            "id": "sub_5_dca7e2",
        },
    ],
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
        },
        "sub_2_30755b": {
            "subtopic_name": "First Generation Computers (1940s-1950s): Vacuum Tubes",
            "slides": [
                {
                    "slide_title": "First Generation Computers: Vacuum Tubes Era",
                    "slide_purpose": "definition",
                    "selected_template": "Title card",
                    "narration_role": "Introduce",
                    "narration_goal": "Learners will understand the basic context and significance of first generation computers and their use of vacuum tubes.",
                    "reasoning": "Starting with a Title card sets a clear, high-impact introduction to the subtopic, providing a concise overview and engaging learners immediately.",
                    "slide_id": "sub_2_30755b_s1",
                },
                {
                    "slide_title": "Vacuum Tubes: Core Technology",
                    "slide_purpose": "intuition",
                    "selected_template": "Image and text",
                    "narration_role": "Interpret",
                    "narration_goal": "Learners will grasp how vacuum tubes functioned as electronic switches and amplifiers in early computers.",
                    "reasoning": "An Image and text template allows detailed narrative explanation paired with a visual of vacuum tubes, building intuitive understanding of their role.",
                    "slide_id": "sub_2_30755b_s2",
                },
                {
                    "slide_title": "Characteristics of Vacuum Tube Computers",
                    "slide_purpose": "definition",
                    "selected_template": "Title with bullets",
                    "narration_role": "Guide",
                    "narration_goal": "Learners will identify key features such as size, speed, heat generation, and reliability of vacuum tube computers.",
                    "reasoning": "Title with bullets efficiently breaks down important characteristics into digestible points, ideal for intermediate learners.",
                    "slide_id": "sub_2_30755b_s3",
                },
                {
                    "slide_title": "Advantages and Limitations of Vacuum Tubes",
                    "slide_purpose": "comparison",
                    "selected_template": "Two columns",
                    "narration_role": "Contrast",
                    "narration_goal": "Learners will compare the pros and cons of vacuum tube technology in early computing.",
                    "reasoning": "Two columns template is perfect for side-by-side comparison, helping learners critically evaluate strengths and weaknesses.",
                    "slide_id": "sub_2_30755b_s4",
                },
                {
                    "slide_title": "Evolution from Vacuum Tubes to Transistors",
                    "slide_purpose": "process",
                    "selected_template": "Timeline",
                    "narration_role": "Connect",
                    "narration_goal": "Learners will understand the historical progression from vacuum tubes to transistors and why this transition was pivotal.",
                    "reasoning": "A timeline visually organizes the historical development, clarifying the process and contextualizing vacuum tubes within computing evolution.",
                    "slide_id": "sub_2_30755b_s5",
                },
                {
                    "slide_title": "Key Takeaways: Vacuum Tube Computers",
                    "slide_purpose": "reinforcement",
                    "selected_template": "Icons with text",
                    "narration_role": "Reinforce",
                    "narration_goal": "Learners will recall essential facts about vacuum tube computers and their impact on early computing history.",
                    "reasoning": "Icons with text provides a visually engaging summary format to reinforce learning with clear, memorable points.",
                    "slide_id": "sub_2_30755b_s6",
                },
            ],
        },
        "sub_3_d87eaf": {
            "subtopic_name": "Second to Fifth Generation Computers (1950s-1980s): Transistors, Integrated Circuits, and Microprocessors",
            "slides": [
                {
                    "slide_title": "Second to Fifth Generation Computers Overview",
                    "slide_purpose": "definition",
                    "selected_template": "Title card",
                    "narration_role": "Introduce",
                    "narration_goal": "Learners will understand the timeline and key technological shifts from the 1950s to 1980s in computer generations.",
                    "reasoning": "Starting with a Title card sets a clear stage for the subtopic, providing a high-impact overview and engaging learners with the importance of these generations.",
                    "slide_id": "sub_3_d87eaf_s1",
                },
                {
                    "slide_title": "Second Generation: Transistor-Based Computers",
                    "slide_purpose": "intuition",
                    "selected_template": "Image and text",
                    "narration_role": "Guide",
                    "narration_goal": "Learners will grasp how transistors replaced vacuum tubes and improved computer performance and reliability.",
                    "reasoning": "Using an Image and text template allows a narrative style with visuals to build intuition about transistor technology and its impact.",
                    "slide_id": "sub_3_d87eaf_s2",
                },
                {
                    "slide_title": "Third Generation: Integrated Circuits Revolution",
                    "slide_purpose": "intuition",
                    "selected_template": "Title with bullets and image",
                    "narration_role": "Interpret",
                    "narration_goal": "Learners will understand the role of integrated circuits in miniaturizing components and enhancing computing power.",
                    "reasoning": "The combination of bullets and image helps explain complex IC concepts with visual support, aiding comprehension of technological advancement.",
                    "slide_id": "sub_3_d87eaf_s3",
                },
                {
                    "slide_title": "Fourth & Fifth Generations: Microprocessors and AI Foundations",
                    "slide_purpose": "definition",
                    "selected_template": "Title with bullets",
                    "narration_role": "Emphasize",
                    "narration_goal": "Learners will identify microprocessor innovation and the emergence of AI concepts in later generations.",
                    "reasoning": "A bullet format clearly breaks down key points about microprocessors and AI foundations, emphasizing their significance in computing evolution.",
                    "slide_id": "sub_3_d87eaf_s4",
                },
                {
                    "slide_title": "Comparing Computer Generations: Key Innovations and Impact",
                    "slide_purpose": "comparison",
                    "selected_template": "Two columns",
                    "narration_role": "Contrast",
                    "narration_goal": "Learners will be able to compare technological features and impacts across the second to fifth generations.",
                    "reasoning": "Two columns facilitate side-by-side comparison of features and impacts, helping learners contrast and consolidate knowledge effectively.",
                    "slide_id": "sub_3_d87eaf_s5",
                },
                {
                    "slide_title": "Summary of Second to Fifth Generation Advances",
                    "slide_purpose": "reinforcement",
                    "selected_template": "Large bullet list",
                    "narration_role": "Reinforce",
                    "narration_goal": "Learners will consolidate their understanding of major technological milestones and their significance in computer history.",
                    "reasoning": "A large bullet list is ideal for summarizing and reinforcing key takeaways, ensuring retention of the main points covered.",
                    "slide_id": "sub_3_d87eaf_s6",
                },
            ],
        },
        "sub_4_c8e0dd": {
            "subtopic_name": "Modern Computer Generations (1980s-present): Artificial Intelligence, Internet, and Beyond",
            "slides": [
                {
                    "slide_title": "Modern Computer Generations Overview",
                    "slide_purpose": "definition",
                    "selected_template": "Title card",
                    "narration_role": "Introduce",
                    "narration_goal": "Learners should understand the scope and significance of modern computer generations from the 1980s to present.",
                    "reasoning": "A Title card slide is ideal for opening the subtopic with a clear and impactful title and a concise hook to set context.",
                    "slide_id": "sub_4_c8e0dd_s1",
                },
                {
                    "slide_title": "Key Technological Advances Since the 1980s",
                    "slide_purpose": "intuition",
                    "selected_template": "Title with bullets and image",
                    "narration_role": "Interpret",
                    "narration_goal": "Learners should grasp the major technological breakthroughs including AI, the Internet, and hardware evolution.",
                    "reasoning": "Combining bullets with an image helps visualize abstract concepts like AI and the Internet, aiding intuition on their impact.",
                    "slide_id": "sub_4_c8e0dd_s2",
                },
                {
                    "slide_title": "Artificial Intelligence Evolution",
                    "slide_purpose": "process",
                    "selected_template": "Timeline",
                    "narration_role": "Guide",
                    "narration_goal": "Learners should understand the chronological development and milestones of AI within modern computing.",
                    "reasoning": "A timeline best illustrates AI\u2019s progressive milestones from early expert systems to deep learning breakthroughs.",
                    "slide_id": "sub_4_c8e0dd_s3",
                },
                {
                    "slide_title": "The Rise of the Internet and Connectivity",
                    "slide_purpose": "process",
                    "selected_template": "Arrows",
                    "narration_role": "Connect",
                    "narration_goal": "Learners should comprehend the cause-effect relationship between networking technologies and global connectivity.",
                    "reasoning": "An arrows template clearly maps the stages from networking protocols to widespread internet adoption and its effects.",
                    "slide_id": "sub_4_c8e0dd_s4",
                },
                {
                    "slide_title": "Comparing AI, Internet, and Emerging Technologies",
                    "slide_purpose": "comparison",
                    "selected_template": "Two columns",
                    "narration_role": "Contrast",
                    "narration_goal": "Learners should differentiate between AI, Internet, and other emerging technologies in terms of function and impact.",
                    "reasoning": "Two columns allow side-by-side comparison of technology categories to clarify distinctions and overlapping capabilities.",
                    "slide_id": "sub_4_c8e0dd_s5",
                },
                {
                    "slide_title": "Future Directions: Beyond Traditional Computing",
                    "slide_purpose": "intuition",
                    "selected_template": "Image and text",
                    "narration_role": "Emphasize",
                    "narration_goal": "Learners should appreciate the emerging frontiers such as quantum computing, edge AI, and pervasive IoT.",
                    "reasoning": "Narrative style with strong visuals helps build intuition about complex future technologies and their potential.",
                    "slide_id": "sub_4_c8e0dd_s6",
                },
                {
                    "slide_title": "Summary of Modern Computer Generations",
                    "slide_purpose": "reinforcement",
                    "selected_template": "Large bullet list",
                    "narration_role": "Reinforce",
                    "narration_goal": "Learners should consolidate their understanding of key concepts, developments, and future trends in modern computing.",
                    "reasoning": "A large bullet list is effective for summarizing and reinforcing the main points covered in the subtopic.",
                    "slide_id": "sub_4_c8e0dd_s7",
                },
            ],
        },
        "sub_5_dca7e2": {
            "subtopic_name": "Comparison and Evolution of Computer Generations",
            "slides": [
                {
                    "slide_title": "Evolution of Computer Generations",
                    "slide_purpose": "definition",
                    "selected_template": "Title card",
                    "narration_role": "Introduce",
                    "narration_goal": "Learners will understand the concept of computer generations and why their evolution is significant in computing history.",
                    "reasoning": "Starting with a Title card sets the stage by clearly defining the subtopic and engaging learners with a concise overview of its importance.",
                    "slide_id": "sub_5_dca7e2_s1",
                },
                {
                    "slide_title": "Key Features of Each Computer Generation",
                    "slide_purpose": "intuition",
                    "selected_template": "Title with bullets and image",
                    "narration_role": "Guide",
                    "narration_goal": "Learners will grasp the distinctive technological advancements and characteristics that define each generation.",
                    "reasoning": "Using bullets with an image helps visualize and intuitively explain the core features of each generation, supporting deeper understanding.",
                    "slide_id": "sub_5_dca7e2_s2",
                },
                {
                    "slide_title": "Timeline of Computer Generations",
                    "slide_purpose": "process",
                    "selected_template": "Timeline",
                    "narration_role": "Connect",
                    "narration_goal": "Learners will be able to place each generation chronologically and recognize the historical progression of computing technology.",
                    "reasoning": "A timeline is ideal for illustrating the sequential development and key milestones across generations, reinforcing temporal context.",
                    "slide_id": "sub_5_dca7e2_s3",
                },
                {
                    "slide_title": "Comparing Computer Generations",
                    "slide_purpose": "comparison",
                    "selected_template": "Two columns",
                    "narration_role": "Contrast",
                    "narration_goal": "Learners will compare and contrast the main differences and improvements between early and later computer generations.",
                    "reasoning": "A two-column layout facilitates direct comparison, making it easier to highlight pros and cons or evolution between generations.",
                    "slide_id": "sub_5_dca7e2_s4",
                },
                {
                    "slide_title": "Summary of Computer Generations Evolution",
                    "slide_purpose": "reinforcement",
                    "selected_template": "Large bullet list",
                    "narration_role": "Reinforce",
                    "narration_goal": "Learners will consolidate their understanding of the key points regarding the evolution and comparison of computer generations.",
                    "reasoning": "A large bullet list is effective for summarizing and reinforcing the main takeaways, aiding retention before concluding the subtopic.",
                    "slide_id": "sub_5_dca7e2_s5",
                },
            ],
        },
    },
}
