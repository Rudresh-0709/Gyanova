try:
    from ..llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from ..state import TutorState
except ImportError:
    # Fallback for direct script execution
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
    from state import TutorState
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def clean_json_output(text: str) -> str:
    """
    Remove code fences and extract JSON cleanly from Gemini.
    """
    text = text.strip()

    # Remove ```json or ``` wrappers
    if text.startswith("```"):
        text = text.strip("`")
        # sometimes gemini sends: ```json\n{ ... }\n```
        text = text.replace("json\n", "", 1).replace("json", "", 1).strip()

    # Find the first { and last }
    import re

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    # fallback: return text as-is
    return text


def should_use_search(slide, subtopic_name):
    llm = load_groq_fast()  # very cheap model

    prompt = f"""
        Decide if external web search (Tavily) is ABSOLUTELY REQUIRED for generating accurate slide narration.

        Use search ONLY when the slide needs:
        - exact facts (dates, numbers, timelines, stats)
        - historical accuracy (events, inventions, discoveries)
        - version/release information
        - real-world data that must be correct and up-to-date

        Do NOT use search for:
        - concepts, explanations, definitions, principles
        - theories, abstractions, analogies
        - content that can be answered from general knowledge

        If accurate narration is possible WITHOUT verified facts, set needs_search to false.

        Respond with ONLY this JSON (no markdown, no code fences):
        {{
        "needs_search": true/false,
        "query": "short search query or empty string"
        }}
        """

    resp = llm.invoke([{"role": "user", "content": prompt}])
    raw = resp.content

    cleaned = clean_json_output(raw)
    try:
        print(cleaned)
        return json.loads(cleaned)
    except:
        return {"needs_search": False, "query": ""}


def generate_narration_for_slide(
    slide, subtopic_name, narration_style, difficulty_level
):
    """Generate spoken narration text for a single slide based on planning metadata."""
    llm = load_openai()

    # Tavily Search Logic
    decision = should_use_search(slide, subtopic_name)
    needs_search = decision.get("needs_search", False)
    search_results = ""

    if needs_search:
        query = decision.get("query", "")
        if query.strip():
            try:
                search = tavily.search(query=query, max_results=5)
                search_results = json.dumps(search, ensure_ascii=False)
            except:
                search_results = "Search failed."

    # Extract Metadata
    narration_role = slide.get("narration_role", "Introduce")
    narration_goal = slide.get("narration_goal", "Explain the concept clearly.")
    selected_template = slide.get("selected_template", "Generic")
    slide_purpose = slide.get("slide_purpose", "Definition")
    slide_title = slide.get("slide_title", "Untitled Slide")

    # ⭐ NEW: Extract Blueprint Constraints
    narration_format = slide.get("narration_format", "points")  # Default to points
    narration_constraints = slide.get("narration_constraints", {})

    # Build format instructions based on blueprint
    format_instruction = ""
    if narration_format == "points":
        point_range = narration_constraints.get("point_count", [3, 5])
        if isinstance(point_range, list):
            format_instruction = (
                f"Provide {point_range[0]}-{point_range[1]} distinct teaching points."
            )
        else:
            format_instruction = f"Provide exactly {point_range} teaching points."
    elif narration_format == "paragraph":
        sentence_range = narration_constraints.get("sentence_count", [3, 5])
        format_instruction = f"Write {sentence_range[0]}-{sentence_range[1]} natural sentences in paragraph form."
    elif narration_format == "narrative":
        sentence_range = narration_constraints.get("sentence_count", [4, 6])
        format_instruction = f"Provide a detailed narrative with {sentence_range[0]}-{sentence_range[1]} flowing sentences."
    elif narration_format == "comparative_points":
        point_range = narration_constraints.get("point_count", [6, 8])
        format_instruction = (
            f"Provide {point_range[0]}-{point_range[1]} points comparing both sides."
        )
    elif narration_format == "sequential_points":
        point_range = narration_constraints.get("point_count", [3, 5])
        format_instruction = f"Provide {point_range[0]}-{point_range[1]} sequential points following the logical flow."
    else:
        format_instruction = "Provide 3-5 clear teaching points or sentences."

    constraint_style = narration_constraints.get("style", "")
    constraint_structure = narration_constraints.get("structure", "")

    SYSTEM_PROMPT = f"""
    You are an expert teacher. Your task is to provide a **spoken narration** for an educational slide.
    
    🎯 CONTEXT:
    - Subtopic: {subtopic_name}
    - Slide Title: {slide_title}
    - Slide Purpose: {slide_purpose}
    - Narration Role: {narration_role}
    - Narration Goal: {narration_goal}
    - Selected Template: {selected_template}
    - Difficulty Level: {difficulty_level}
    - Narration Style (User Preference): {narration_style}
    
    {"🔍 VERIFIED FACTS (Use these for accuracy):\n" + search_results if needs_search else ""}
    
    ⭐ BLUEPRINT CONSTRAINTS:
    - Format Required: {narration_format}
    - {format_instruction}
    {f"- Style Guidance: {constraint_style}" if constraint_style else ""}
    {f"- Structure Note: {constraint_structure}" if constraint_structure else ""}

    🧩 NARRATION RULES:
    1. **Spoken Only**: Write exactly what the teacher would say. Do NOT write bullet points or slide text.
    2. **Format Compliance**: STRICTLY follow the format requirement above ({narration_format}).
    3. **Role-Driven**:
       - 'Introduce': Set the hook, explain why this matters, and define the scope.
       - 'Interpret': Explain the relationships or the 'why' behind what is shown.
       - 'Guide': Lead the learner through a sequence or logical flow.
       - 'Contrast': Highlight differences, pros/cons, or trade-offs.
       - 'Reinforce': Tie it all together and cement the key takeaway.
    4. **Template Aware**: Assume the visual structure (e.g., a {selected_template}) is already on screen. Do NOT describe the layout (e.g., don't say 'On the left we see...'). Instead, explain the logic of the content.
    5. **Style & Difficulty**: Strictly follow the style '{narration_style}' and ensure the complexity matches '{difficulty_level}'.
    
    ⛔ DON'Ts:
    - Do NOT say "In this slide" or "Moving on to...".
    - Do NOT use markdown formatting.
    - Do NOT repeat the slide title.

    OUTPUT FORMAT:
    Output ONLY valid JSON:
    {{
      "slide_title": "{slide_title}",
      "narration_text": "The spoken script..."
    }}
    """

    user_prompt = f"Generate narration for the slide: '{slide_title}'."

    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    try:
        cleaned = clean_json_output(response.content)
        return json.loads(cleaned)
    except Exception:
        return {
            "slide_title": slide_title,
            "narration_text": "I'll explain this concept simply: " + narration_goal,
        }


def generate_narrations_batch(slides, subtopic_name, narration_style, difficulty_level):
    """
    Generate narrations for all slides in a subtopic using optimized batch approach.
    Uses style-neutral examples to show length/structure without biasing content.
    """
    llm = load_openai()

    # STYLE-NEUTRAL EXAMPLES (show length/structure, NOT style)
    STYLE_NEUTRAL_EXAMPLES = f"""
⚠️ THESE EXAMPLES SHOW TARGET LENGTH AND STRUCTURE ONLY - NOT STYLE!

EXAMPLE 1 - Paragraph Format (142 words):
Slide: "Introduction to Topic X"
Narration: "Topic X represents a fundamental concept in this domain. It can be defined as the systematic approach to solving problems through structured methodology. This concept emerged during the period when researchers recognized the need for standardized processes. Understanding Topic X is important because it provides a framework for analysis, enables consistent results across different contexts, and forms the foundation for more advanced concepts. When we examine Topic X in detail, we observe three key characteristics: first, it emphasizes systematic organization; second, it relies on verifiable principles; third, it produces reproducible outcomes. These characteristics distinguish it from alternative approaches that may be less structured. By mastering Topic X, learners will be able to apply these principles in practical situations and recognize when this approach is most appropriate."

EXAMPLE 2 - Points Format (156 words):
Slide: "How Process Y Works"
Narration: "Process Y operates through a series of distinct stages. First, the initial phase involves gathering necessary inputs and establishing baseline parameters, which sets the foundation for subsequent operations. Second, the transformation stage applies specific procedures to modify the inputs according to predetermined rules, ensuring consistency and accuracy throughout the process. Third, the validation phase checks that outputs meet required specifications, identifying any deviations that need correction. Fourth, the integration stage combines validated outputs with existing systems, maintaining compatibility and functionality. Finally, the optimization cycle reviews overall performance and identifies opportunities for improvement, creating a feedback loop that enhances future iterations. Each stage plays a critical role in ensuring the process functions correctly. Understanding these stages helps learners grasp both the technical mechanics and the logical flow of the overall process."

📝 KEY OBSERVATION: Notice both examples are 120-180 words and provide COMPLETE explanations.
Your narrations should match this LENGTH and DEPTH, but use the user's specified style: "{narration_style}"
"""

    # Build slide info blocks with strong separators
    slides_info = []
    for i, slide in enumerate(slides, 1):
        narration_format = slide.get("narration_format", "points")
        slide_block = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SLIDE {i} OF {len(slides)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 METADATA:
- Title: {slide.get('slide_title')}
- Purpose: {slide.get('slide_purpose')}
- Role: {slide.get('narration_role')}
- Goal: {slide.get('narration_goal')}
- Format: {narration_format} ({'paragraph' if narration_format == 'paragraph' else 'distinct teaching points'})
- Constraints: {slide.get('narration_constraints', {})}

⚠️ REQUIREMENTS FOR THIS SLIDE:
1. Write 120-180 WORDS (count carefully!)
2. Treat INDEPENDENTLY (no "as mentioned before", "in this slide")
3. Follow role: {slide.get('narration_role')}
4. Use THIS style: {narration_style}
5. Format: {narration_format}
"""
        slides_info.append(slide_block)

    # Build batch prompt with style-neutral examples
    BATCH_PROMPT = f"""
You are an expert teacher creating spoken narrations for a lesson.

🎯 CONTEXT:
- Subtopic: {subtopic_name}
- Difficulty: {difficulty_level}
- Narration Style: {narration_style}
- Total Slides: {len(slides)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 LENGTH & STRUCTURE EXAMPLES (NOT STYLE EXAMPLES!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{STYLE_NEUTRAL_EXAMPLES}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎭 CRITICAL: YOUR STYLE TO USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The examples above show LENGTH (120-180 words) and STRUCTURE requirements ONLY.

✅ DO copy: Word count, depth of explanation, completeness
❌ DO NOT copy: Tone, word choice, or writing approach from examples

✅ YOUR NARRATIONS MUST USE THIS STYLE: "{narration_style}"

Let the user's style guide ALL aspects of your writing:
- Word choice and vocabulary
- Sentence structure and flow  
- Tone and personality
- Teaching approach

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ CRITICAL INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **LENGTH**: Each narration MUST be 120-180 words
   - This equals 60-90 seconds of spoken content
   - Provide COMPLETE, DETAILED explanations (not summaries)
   
2. **INDEPENDENCE**: Process each slide SEPARATELY
   - Don't say "as mentioned before", "next we'll see", "in this slide"
   - Each narration stands alone as a teaching moment
   
3. **STYLE CONSISTENCY**: Use "{narration_style}" for ALL slides
   - Maintain this style throughout every single narration
   
4. **FORMAT COMPLIANCE**: Follow each slide's required format
   - "paragraph": Natural flowing sentences
   - "points": Distinct teaching points (First... Second... Third...)
   - "sequential_points": Step-by-step progression
   - "comparative_points": Balanced comparison
   
5. **QUALITY**: Be thorough, engaging, pedagogically effective
   - Adapt to slide purpose (definition, visualization, process, etc.)
   - Use appropriate techniques for the content type

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 SLIDES TO NARRATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join(slides_info)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (JSON):
{{
  "narrations": [
    {{
      "slide_number": 1,
      "slide_title": "...",
      "narration_text": "...",
      "word_count": <actual word count>
    }},
    ...
  ]
}}

REMEMBER: 120-180 words per narration. Style: "{narration_style}" (NOT the example style!)
"""

    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are an expert educational content generator focused on quality and depth.",
            },
            {"role": "user", "content": BATCH_PROMPT},
        ]
    )

    # Parse and validate
    try:
        cleaned = clean_json_output(response.content)
        batch_result = json.loads(cleaned)
        narrations = batch_result.get("narrations", [])

        results = []
        regeneration_count = 0

        for i, slide in enumerate(slides):
            if i < len(narrations):
                narration_text = narrations[i].get("narration_text", "")
                word_count = len(narration_text.split())

                # Quality gate: regenerate if too short
                if word_count < 80:
                    print(
                        f"  ⚠️  Slide {i+1} too short ({word_count} words) - regenerating individually..."
                    )
                    individual_result = generate_narration_for_slide(
                        slide, subtopic_name, narration_style, difficulty_level
                    )
                    narration_data = {
                        "narration_text": individual_result.get("narration_text", ""),
                        "regenerated": True,
                    }
                    regeneration_count += 1
                else:
                    narration_data = {
                        "narration_text": narration_text,
                        "regenerated": False,
                    }
            else:
                # Missing from batch - regenerate
                print(
                    f"  ⚠️  Slide {i+1} missing from batch - regenerating individually..."
                )
                individual_result = generate_narration_for_slide(
                    slide, subtopic_name, narration_style, difficulty_level
                )
                narration_data = {
                    "narration_text": individual_result.get("narration_text", ""),
                    "regenerated": True,
                }
                regeneration_count += 1

            results.append({**slide, **narration_data})

        if regeneration_count > 0:
            print(
                f"  ✓ Regenerated {regeneration_count}/{len(slides)} slides individually"
            )

        return results

    except Exception as e:
        # Full fallback: regenerate all individually
        print(
            f"  ❌ Batch generation failed ({e}) - falling back to individual generation"
        )
        results = []
        for slide in slides:
            individual_result = generate_narration_for_slide(
                slide, subtopic_name, narration_style, difficulty_level
            )
            results.append({**slide, **individual_result})
        return results


def generate_all_narrations(state: TutorState):
    """Processes the slide_plan to generate spoken narrations using optimized batch approach."""
    slide_plan = state.get("slide_plan", {})
    narration_style = state.get(
        "narration_style", "Clear and engaging educational style"
    )
    difficulty = state.get("difficulty", "Beginner")

    # We will store final slide objects in state["slides"]
    if "slides" not in state or not isinstance(state["slides"], dict):
        state["slides"] = {}

    for sub_id, plan_entry in slide_plan.items():
        subtopic_name = plan_entry.get("subtopic_name")
        planned_slides = plan_entry.get("slides", [])

        print(
            f"\n📚 Generating narrations for: {subtopic_name} ({len(planned_slides)} slides)"
        )

        # Use optimized batch generation
        generated_slides = generate_narrations_batch(
            slides=planned_slides,
            subtopic_name=subtopic_name,
            narration_style=narration_style,
            difficulty_level=difficulty,
        )

        state["slides"][sub_id] = generated_slides

    return state


if __name__ == "__main__":
    SampleState = {
        "topic": "Computer generations",
        "difficulty": "Intermediate",
        "narration_style": "Friendly and analogies-heavy teacher style",
        "slide_plan": {
            "sub_1_2b67b6": {
                "subtopic_name": "Introduction to Computer Generations",
                "slides": [
                    {
                        "slide_title": "Introduction to Computer Generations",
                        "slide_purpose": "definition",
                        "selected_template": "Title card",
                        "narration_role": "Introduce",
                        "narration_goal": "Understand what computer generations are and why they matter.",
                        "reasoning": "Standard intro style.",
                        "slide_id": "sub_1_2b67b6_s1",
                    }
                ],
            }
        },
    }

    updated_state = generate_all_narrations(SampleState)
    print(json.dumps(updated_state, indent=2))
