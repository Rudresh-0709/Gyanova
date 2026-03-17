import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Import the LangGraph workflow
from app.services.langgraphflow import planning_graph, full_graph

router = APIRouter()
logger = logging.getLogger(__name__)

import json
import os

# Simple in-memory task store with file persistence
TASKS_FILE = "tasks.json"
tasks_db: Dict[str, Dict[str, Any]] = {}

def load_tasks():
    global tasks_db
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                tasks_db = json.load(f)
            logger.info(f"Loaded {len(tasks_db)} tasks from {TASKS_FILE}")
        except Exception as e:
            logger.error(f"Failed to load tasks from {TASKS_FILE}: {e}")
            tasks_db = {}

def save_tasks():
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks_db, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save tasks to {TASKS_FILE}: {e}")

# Initial load
load_tasks()


class GenerateLessonRequest(BaseModel):
    topic: str
    current_level: str = "Intermediate"
    learning_goal: str = "Understand Core Concepts"
    granularity: str = "Detailed"
    preferred_method: str = "Socratic"
    teacher_gender: str = "Female"


class ConfirmPlanRequest(BaseModel):
    topic: Optional[str] = None
    sub_topics: Optional[List[Dict[str, Any]]] = None
    plans: Dict[str, Any]


async def run_planning_task(task_id: str, request: GenerateLessonRequest):
    logger.info(f"Starting planning task {task_id} for topic: {request.topic}")
    tasks_db[task_id]["status"] = "planning"
    save_tasks()

    try:
        initial_state = {
            "user_input": request.topic,
            "topic": "",
            "difficulty": request.current_level,
            "granularity": request.granularity,
            "sub_topics": [],
            "plans": {},
            "slides": {},
            "intro_text": "",
            "messages": [],
        }

        # Initialize result in tasks_db
        tasks_db[task_id]["result"] = initial_state

        # Use streaming to get incremental updates from nodes
        async for chunk in planning_graph.astream(initial_state):
            for node_name, state_update in chunk.items():
                if "messages" in state_update:
                    del state_update["messages"]

                # Update the result incrementally
                tasks_db[task_id]["result"].update(state_update)
                logger.info(f"  ⚡ Phase 1: Update from {node_name} for task {task_id}")

        tasks_db[task_id]["status"] = "planning_completed"
        logger.info(f"Planning for {task_id} completed successfully.")
        save_tasks()

    except Exception as e:
        logger.error(f"Planning task {task_id} failed: {str(e)}", exc_info=True)
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)
        save_tasks()


async def run_generation_task(task_id: str, request: ConfirmPlanRequest):
    logger.info(f"Starting full generation task {task_id}")
    tasks_db[task_id]["status"] = "processing"
    save_tasks()

    try:
        # Resume from the previous state but with confirmed/modified plans
        current_state = tasks_db[task_id]["result"]

        if request.topic:
            current_state["topic"] = request.topic
        if request.sub_topics:
            current_state["sub_topics"] = request.sub_topics

        current_state["plans"] = request.plans

        # Run Phase 2 (Streaming for incremental updates)
        async for chunk in full_graph.astream(current_state):
            # chunk is {node_name: state_update}
            for node_name, state_update in chunk.items():
                if "messages" in state_update:
                    del state_update["messages"]

                # Update the result incrementally
                tasks_db[task_id]["result"].update(state_update)
                logger.info(
                    f"  ⚡ Incremental update from {node_name} for mission {task_id}"
                )
                save_tasks()

        tasks_db[task_id]["status"] = "completed"
        logger.info(f"Generation for {task_id} completed successfully.")
        save_tasks()

    except Exception as e:
        logger.error(f"Generation task {task_id} failed: {str(e)}", exc_info=True)
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)
        save_tasks()


@router.post("/")
async def generate_lesson(
    request: GenerateLessonRequest, background_tasks: BackgroundTasks
):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending"}
    save_tasks()

    background_tasks.add_task(run_planning_task, task_id, request)
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Lesson planning started.",
    }


@router.post("/{task_id}/confirm")
async def confirm_plan(
    task_id: str, request: ConfirmPlanRequest, background_tasks: BackgroundTasks
):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] != "planning_completed":
        logger.warning(
            f"Confirm attempted for task {task_id} but status is {task['status']}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Can only confirm a completed plan. Current status: {task['status']}",
        )

    background_tasks.add_task(run_generation_task, task_id, request)
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Generation started.",
    }


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found in database.")
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        # Shallow copy to avoid modifying the actual DB in-memory
        resp = {"task_id": task_id, **task}
        return resp
    except Exception as e:
        logger.error(f"Error preparing task status response for {task_id}: {str(e)}")
        # If the full object fails to serialize, try returning just the status
        return {
            "task_id": task_id,
            "status": task.get("status"),
            "error": "Serialization error",
        }
