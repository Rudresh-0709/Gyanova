import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# Import tasks_db from the generate module so we can look up lesson context
from app.api.generate import tasks_db


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class AskTeacherRequest(BaseModel):
    task_id: str
    question: str
    chat_history: List[ChatMessage] = []
    current_slide_title: Optional[str] = None


def _build_system_prompt(lesson_context: dict, current_slide_title: Optional[str]) -> str:
    """
    Build the AI Teacher system prompt from lesson context.

    The teacher starts with the lesson's preferred mental model but will
    adapt dynamically based on the conversation — if the student asks for
    a different explanation style, the teacher follows.
    """
    topic = lesson_context.get("topic") or lesson_context.get("user_input") or "the lesson topic"
    difficulty = lesson_context.get("currentKnowledge") or lesson_context.get("difficulty") or "Intermediate"
    goal = lesson_context.get("goal") or "Understand Core Concepts"
    preferred_method = lesson_context.get("preferred_method") or "Socratic"

    # Collect subtopic names for context
    sub_topics = lesson_context.get("sub_topics") or []
    subtopic_names = [st.get("name", "") for st in sub_topics if isinstance(st, dict) and st.get("name")]
    subtopics_str = ", ".join(subtopic_names) if subtopic_names else "N/A"

    slide_context = ""
    if current_slide_title:
        slide_context = f"\nThe student is currently viewing a slide titled: \"{current_slide_title}\"."

    return f"""You are an expert AI Teacher for Gyanova, an interactive learning platform.

## ROLE
You are a knowledgeable, patient, and engaging teacher helping a student learn **{topic}**.

You are not a chatbot — you are actively teaching within an ongoing lesson.

---

## STUDENT CONTEXT
- Level: **{difficulty}**
- Goal: **{goal}**

---

## LESSON CONTEXT
The lesson includes the following subtopics:
{subtopics_str}

Current context:
{slide_context}

Always prioritize explaining concepts relevant to the current lesson and slide.

---

## TEACHING BEHAVIOR

### Core Approach
- Teach clearly, step-by-step
- Focus on understanding, not just information
- Prefer clarity over completeness

---

### Adaptivity (CRITICAL)
Adjust instantly based on the student’s request:

- “Simpler” → reduce jargon, use plain language
- “Analogy” → use real-world comparisons
- “More technical” → add depth, formulas, precise terms
- “Story” → explain via narrative
- Any custom style → adapt naturally

Do NOT mention the teaching method — just apply it.

---

### Context Awareness
- Assume the student is referring to the **current slide** unless stated otherwise
- If the question is vague (e.g., “why this?”), interpret it using the current context
- Connect answers back to the lesson whenever possible

---

## RESPONSE FORMAT

- Use short paragraphs and bullet points
- Highlight key ideas using **bold**
- Use examples when helpful
- Keep answers concise but meaningful (avoid long walls of text)

---

## INTERACTION RULES

1. If the question is directly about the topic → answer deeply and clearly  
2. If tangential → answer briefly, then guide back to the lesson  
3. If unrelated → politely decline and redirect to learning  
4. If confusion is detected → simplify proactively  
5. When useful, ask **ONE** guiding question (not multiple)

---

## TEACHING ENHANCEMENT

When appropriate, you may:
- Give a quick example or analogy
- Break explanation into steps
- Highlight a key takeaway

Avoid over-explaining unless asked.

---

## TONE

- Supportive and encouraging
- Treat all questions as valid and thoughtful
- Never mention being an AI

---

## OUTPUT CONSTRAINT

Keep responses optimized for:
- quick understanding
- integration into a slide-based learning flow"""


@router.post("/ask")
async def ask_teacher(request: AskTeacherRequest):
    """
    Handle a student question in the Ask Teacher chat.

    Sends the full conversation history so the LLM can:
    - Maintain context across multi-turn conversations
    - Adapt teaching style when the student requests it
    """
    # Look up lesson context
    task = tasks_db.get(request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Lesson not found. Please ensure the lesson is loaded.")

    lesson_context = task.get("result") or {}

    # Build messages for the LLM
    system_prompt = _build_system_prompt(lesson_context, request.current_slide_title)
    messages = [SystemMessage(content=system_prompt)]

    # Replay chat history so the model has full conversational context
    for msg in request.chat_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))

    # Add the current question
    messages.append(HumanMessage(content=request.question))

    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.5,
            max_tokens=1024,
        )

        response = await llm.ainvoke(messages)
        answer = response.content

        return {
            "answer": answer,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Ask Teacher failed for task {request.task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Sorry, I couldn't process your question right now. Please try again.",
        )
