import logging
import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# Import tasks_db from the generate module so we can look up lesson context
from app.api.generate import tasks_db


class QuizGenerateRequest(BaseModel):
    task_id: str
    subtopic_id: str


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_index: int
    explanation: str
    related_slide_id: str
    related_concept: str


class QuizResponse(BaseModel):
    quiz_id: str
    subtopic_name: str
    questions: List[QuizQuestion]


def _extract_subtopic_context(lesson_result: dict, subtopic_id: str) -> dict:
    """
    Extract all relevant slide content for a subtopic to feed into the quiz
    generation prompt.

    Returns a dict with:
      - subtopic_name: str
      - slides: list of {slide_id, title, summary, narration_text, key_facts}
    """
    sub_topics = lesson_result.get("sub_topics") or []
    subtopic_name = ""
    for st in sub_topics:
        if isinstance(st, dict) and st.get("id") == subtopic_id:
            subtopic_name = st.get("name", "")
            break

    plans = lesson_result.get("plans", {}).get(subtopic_id, [])
    slides_data = lesson_result.get("slides", {}).get(subtopic_id, [])

    slide_contexts = []
    for i, slide in enumerate(slides_data):
        if not isinstance(slide, dict):
            continue

        slide_id = slide.get("slide_id", f"slide_{i}")
        title = slide.get("title", "")
        summary = slide.get("summary") or slide.get("objective", "")
        narration_text = slide.get("narration_text", "")
        key_facts = slide.get("key_facts", [])

        # Also extract narration segment texts for richer context
        segments = slide.get("narration_segments", [])
        segment_texts = []
        if isinstance(segments, list):
            for seg in segments:
                if isinstance(seg, dict) and seg.get("text"):
                    segment_texts.append(seg["text"])

        # Grab coverage_contract and must_cover for richer quiz material
        coverage = slide.get("coverage_contract", "")
        must_cover = slide.get("must_cover", [])

        slide_contexts.append({
            "slide_id": slide_id,
            "title": title,
            "summary": summary,
            "narration_text": narration_text,
            "key_facts": key_facts if isinstance(key_facts, list) else [],
            "segment_texts": segment_texts,
            "coverage_contract": coverage,
            "must_cover": must_cover if isinstance(must_cover, list) else [],
        })

    return {
        "subtopic_name": subtopic_name,
        "slides": slide_contexts,
    }


def _build_quiz_prompt(subtopic_context: dict) -> str:
    """
    Build the system prompt for quiz generation.
    """
    subtopic_name = subtopic_context["subtopic_name"]
    slides = subtopic_context["slides"]

    # Build a condensed representation of all slide content
    slides_text = ""
    for s in slides:
        slides_text += f"\n--- Slide: {s['title']} (ID: {s['slide_id']}) ---\n"
        if s["summary"]:
            slides_text += f"Summary: {s['summary']}\n"
        if s["coverage_contract"]:
            slides_text += f"Coverage: {s['coverage_contract']}\n"
        if s["must_cover"]:
            slides_text += f"Must Cover: {', '.join(str(x) for x in s['must_cover'])}\n"
        if s["key_facts"]:
            slides_text += f"Key Facts: {', '.join(str(x) for x in s['key_facts'])}\n"
        if s["narration_text"]:
            slides_text += f"Narration: {s['narration_text'][:500]}\n"
        elif s["segment_texts"]:
            combined = " ".join(s["segment_texts"])[:500]
            slides_text += f"Narration: {combined}\n"

    return f"""You are a quiz generator for an interactive learning platform called Gyanova.

## TASK
Generate exactly 5 multiple-choice questions that test the student's understanding of the subtopic: **{subtopic_name}**

## SOURCE MATERIAL
The following slides were taught to the student:
{slides_text}

## RULES

1. Each question MUST test a concept directly covered in the slides above.
2. Each question MUST have exactly 4 options (A, B, C, D).
3. Exactly ONE option must be correct.
4. The `explanation` should clearly explain WHY the correct answer is right (2-3 sentences).
5. The `related_slide_id` MUST be the exact slide_id from the source material that covers the tested concept.
6. The `related_concept` should be a short label of what concept the question tests (e.g., "Convolution Operation", "Activation Functions").
7. Questions should progress from basic recall to application/understanding.
8. Distractors (wrong options) should be plausible but clearly wrong.
9. Avoid trick questions — the goal is to reinforce learning, not confuse.
10. Keep question text concise and clear.

## OUTPUT FORMAT
Return a JSON array of question objects. Each object must have these exact keys:
- "id": string (e.g., "q1", "q2", ...)
- "question": string
- "options": array of 4 strings
- "correct_index": integer (0-3, index of the correct option)
- "explanation": string
- "related_slide_id": string (exact slide_id from source)
- "related_concept": string

Return ONLY the JSON array, no markdown fences, no explanation outside the array."""


@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest):
    """
    Generate a quiz for a completed subtopic.

    Extracts slide content from the lesson and uses an LLM to produce
    structured MCQ questions linked to specific slides.
    """
    # Look up lesson context
    task = tasks_db.get(request.task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found. Please ensure the lesson is loaded.",
        )

    lesson_result = task.get("result") or {}

    # Validate that the subtopic has slide content
    slides_for_sub = lesson_result.get("slides", {}).get(request.subtopic_id, [])
    if not slides_for_sub:
        raise HTTPException(
            status_code=400,
            detail=f"No slides found for subtopic '{request.subtopic_id}'. Quiz requires completed slides.",
        )

    # Extract context
    subtopic_context = _extract_subtopic_context(lesson_result, request.subtopic_id)

    if not subtopic_context["slides"]:
        raise HTTPException(
            status_code=400,
            detail="No slide content available for quiz generation.",
        )

    # Build prompt and call LLM
    system_prompt = _build_quiz_prompt(subtopic_context)

    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.4,
            max_tokens=2048,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate the quiz now."),
        ]

        response = await llm.ainvoke(messages)
        raw_content = response.content.strip()

        # Strip markdown code fences if present
        if raw_content.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            lines = raw_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_content = "\n".join(lines)

        questions_data = json.loads(raw_content)

        # Validate and normalize
        questions = []
        for i, q in enumerate(questions_data):
            if not isinstance(q, dict):
                continue

            # Ensure correct_index is valid
            correct_idx = int(q.get("correct_index", 0))
            options = q.get("options", [])
            if correct_idx < 0 or correct_idx >= len(options):
                correct_idx = 0

            questions.append(QuizQuestion(
                id=q.get("id", f"q{i + 1}"),
                question=q.get("question", ""),
                options=options[:4],  # Ensure max 4 options
                correct_index=correct_idx,
                explanation=q.get("explanation", ""),
                related_slide_id=q.get("related_slide_id", ""),
                related_concept=q.get("related_concept", ""),
            ))

        if not questions:
            raise ValueError("LLM returned no valid questions")

        quiz_id = f"quiz_{request.subtopic_id}_{uuid.uuid4().hex[:8]}"

        return QuizResponse(
            quiz_id=quiz_id,
            subtopic_name=subtopic_context["subtopic_name"],
            questions=questions[:5],  # Cap at 5
        )

    except json.JSONDecodeError as e:
        logger.error(
            f"Quiz generation JSON parse error for {request.subtopic_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to parse quiz from AI. Please try again.",
        )
    except Exception as e:
        logger.error(
            f"Quiz generation failed for task {request.task_id}, subtopic {request.subtopic_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Sorry, I couldn't generate the quiz right now. Please try again.",
        )
