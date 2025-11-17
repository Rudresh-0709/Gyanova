from ...llm.model_loader import load_groq, load_groq_fast, load_openai, load_gemini
from ...state import TutorState
import json

llm = load_openai()

SYSTEM_PROMPT = """
You are an AI content-visualization generator.
Your task is to create the contentBlocks JSON array for a slide.
Do NOT rewrite the title or narration.
Use the title + narration points ONLY as context.

Input you will receive:

slide_title

narration_points

Your task:

Generate ONLY:

"contentBlocks": [ ... ]

Rules for generation:

Choose 1 or 2 content types that best fit the narration.
Allowed types:

explanation

timeline

comparison

steps

statistics

story

takeaways

Use only valid combinations:

narration + explanation

narration + timeline

narration + comparison

narration + statistics

narration + steps

narration + takeaways

OR only one block type (explanation / timeline / etc.)

NEVER use invalid combinations:

timeline + comparison

statistics + comparison

timeline + steps

statistics + steps

any 3-block mix

Output ONLY the contentBlocks array, nothing else.

JSON must be valid and must follow EXACT type formats:

Type Formats to Follow:
✔ EXPLANATION
{
  "type": "explanation",
  "paragraphs": [
    "..."
  ]
}

✔ TIMELINE
{
  "type": "timeline",
  "events": [
    { "year": "", "description": "" }
  ]
}

✔ COMPARISON
{
  "type": "comparison",
  "columns": [
    { "title": "", "items": [""] },
    { "title": "", "items": [""] }
  ]
}

✔ STEPS
{
  "type": "steps",
  "steps": [
    { "step": 1, "title": "", "description": "" }
  ]
}

✔ STATISTICS
{
  "type": "statistics",
  "stats": [
    { "label": "", "value": "" }
  ]
}

✔ STORY
{
  "type": "story",
  "text": ""
}

✔ TAKEAWAYS
{
  "type": "takeaways",
  "points": ["", ""]
}

Now produce the output using this format:

Expected Response:

{
  "contentBlocks": [
    ...
  ]
}


No title.
No narration.
No explanation text outside the blocks.
Only the contentBlocks array.
"""

USER_PROMPT = f"""Using the rules from the system prompt, generate the contentBlocks for this slide.

slide_title: Future of Computing

narration_points:
[
    "Fifth Generation focuses on AI, parallel processing, and nanotechnology for advanced computing.",
    "AI enables machines to learn, reason, and make decisions like humans.",
    "Parallel processing enhances speed by performing multiple tasks simultaneously.",
    "Nanotechnology involves building devices at the molecular level for powerful computing capabilities.",
    "The future of computing lies in combining these technologies for unprecedented advancements.",
]

Output ONLY the contentBlocks JSON object."""

response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]
    )

print(json.loads(response.content))