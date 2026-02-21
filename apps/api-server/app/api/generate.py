import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import the LangGraph workflow
from app.services.langgraphflow import compiled_graph

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-memory task store for MVP
# In a real app, use Redis or a database
tasks_db: Dict[str, Dict[str, Any]] = {}


class GenerateLessonRequest(BaseModel):
    topic: str
    current_level: str = "Intermediate"
    learning_goal: str = "Understand Core Concepts"
    granularity: str = "Detailed"
    preferred_method: str = "Socratic"
    teacher_gender: str = "Female"


def run_langgraph_task(task_id: str, request: GenerateLessonRequest):
    logger.info(f"Starting background task {task_id} for topic: {request.topic}")
    tasks_db[task_id]["status"] = "processing"

    try:
        initial_state = {
            "user_input": request.topic,
            "topic": "",
            "granularity": request.granularity,
            "sub_topics": [],
            "slides": {},
            "intro_text": "",
            "messages": [],
        }

        final_state = compiled_graph.invoke(initial_state)

        if "messages" in final_state:
            del final_state["messages"]

        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["result"] = final_state
        logger.info(f"Task {task_id} completed successfully.")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)


@router.post("/")
async def generate_lesson(
    request: GenerateLessonRequest, background_tasks: BackgroundTasks
):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending"}

    background_tasks.add_task(run_langgraph_task, task_id, request)
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Lesson generation started.",
    }


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, **task}
