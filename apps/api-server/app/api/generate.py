import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum

# Import the LangGraph workflow
from app.services.langgraphflow import planning_graph, full_graph

router = APIRouter()
logger = logging.getLogger(__name__)

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime

# Simple in-memory task store with file persistence
# We place these in a hidden folder in the root to avoid triggering Next.js dev reloads
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_ROOT = ROOT_DIR / ".persistent_data"
os.makedirs(DATA_ROOT, exist_ok=True)

TASKS_FILE = os.path.join(DATA_ROOT, "tasks.json")
TASK_STATE_DIR = os.path.join(DATA_ROOT, "task_states")
tasks_db: Dict[str, Dict[str, Any]] = {}


def _merge_slide_lists(existing: Any, incoming: Any) -> List[Dict[str, Any]]:
    """Merge slide updates by slide_id to avoid overwriting concurrent fields."""
    existing_list = existing if isinstance(existing, list) else []
    incoming_list = incoming if isinstance(incoming, list) else []

    merged: List[Dict[str, Any]] = []
    existing_by_id: Dict[str, Dict[str, Any]] = {}

    for item in existing_list:
        if not isinstance(item, dict):
            continue
        cloned = dict(item)
        slide_id = cloned.get("slide_id")
        if isinstance(slide_id, str) and slide_id:
            existing_by_id[slide_id] = cloned
        merged.append(cloned)

    for item in incoming_list:
        if not isinstance(item, dict):
            continue
        incoming_slide = dict(item)
        slide_id = incoming_slide.get("slide_id")
        if isinstance(slide_id, str) and slide_id and slide_id in existing_by_id:
            existing_by_id[slide_id].update(incoming_slide)
        else:
            merged.append(incoming_slide)
            if isinstance(slide_id, str) and slide_id:
                existing_by_id[slide_id] = incoming_slide

    return merged


def _has_preview_content(result: Dict[str, Any]) -> bool:
    """Preview is ready when at least one intro or slide HTML document is renderable."""
    lesson_intro = result.get("lesson_intro_narration") or {}
    if isinstance(lesson_intro, dict) and isinstance(lesson_intro.get("html_doc"), str):
        if lesson_intro["html_doc"].strip():
            return True

    subtopic_intros = result.get("subtopic_intro_narrations") or {}
    if isinstance(subtopic_intros, dict):
        for intro in subtopic_intros.values():
            if isinstance(intro, dict) and isinstance(intro.get("html_doc"), str):
                if intro["html_doc"].strip():
                    return True

    slides = result.get("slides") or {}
    if isinstance(slides, dict):
        for slide_list in slides.values():
            if not isinstance(slide_list, list):
                continue
            for slide in slide_list:
                if not isinstance(slide, dict):
                    continue
                html = slide.get("html_content")
                if isinstance(html, str) and html.strip():
                    return True

    return False


def _merge_generation_state(current_result: Dict[str, Any], state_update: Dict[str, Any]) -> None:
    """
    Reducer-style merge: merge nested structures deterministically so parallel
    workers can update isolated fields without clobbering sibling updates.
    """
    new_state = _json_safe(state_update)

    incoming_slides = new_state.pop("slides", None)
    if isinstance(incoming_slides, dict):
        current_slides = current_result.setdefault("slides", {})
        if not isinstance(current_slides, dict):
            current_slides = {}
            current_result["slides"] = current_slides
        for sub_id, slide_list in incoming_slides.items():
            current_slides[sub_id] = _merge_slide_lists(current_slides.get(sub_id), slide_list)

    incoming_subtopic_intros = new_state.pop("subtopic_intro_narrations", None)
    if isinstance(incoming_subtopic_intros, dict):
        current_intros = current_result.setdefault("subtopic_intro_narrations", {})
        if not isinstance(current_intros, dict):
            current_intros = {}
            current_result["subtopic_intro_narrations"] = current_intros
        for sub_id, intro_payload in incoming_subtopic_intros.items():
            if isinstance(intro_payload, dict) and isinstance(current_intros.get(sub_id), dict):
                current_intros[sub_id].update(intro_payload)
            else:
                current_intros[sub_id] = intro_payload

    incoming_lesson_intro = new_state.pop("lesson_intro_narration", None)
    if isinstance(incoming_lesson_intro, dict):
        current_lesson_intro = current_result.get("lesson_intro_narration")
        if isinstance(current_lesson_intro, dict):
            current_lesson_intro.update(incoming_lesson_intro)
        else:
            current_result["lesson_intro_narration"] = incoming_lesson_intro

    current_result.update(new_state)


def _json_safe(value: Any) -> Any:
    """
    Recursively convert any value to a JSON-serializable form.
    
    Handles:
    - Primitives (str, int, float, bool, None)
    - Dicts (filtering keys starting with '_')
    - Lists, tuples, sets
    - Dataclasses (converts to dict via asdict)
    - Enums (converts to their value)
    - Objects with __dict__ (converts to dict)
    - Fallback: converts to string
    
    Special behavior:
    - Drops all dict keys starting with '_' (transient/private fields)
    - Converts Enum instances to their values
    - If a ComposedSlide or similar non-serializable object leaks into state,
      this will safely convert it rather than crash
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # Handle Enums (including from GyML definitions like Emphasis)
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        safe_dict = {}
        for key, item in value.items():
            # Drop transient/internal fields from persisted task state.
            if isinstance(key, str) and key.startswith("_"):
                continue
            safe_dict[key] = _json_safe(item)
        return safe_dict

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    if is_dataclass(value):
        return _json_safe(asdict(value))

    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))

    # Fallback: convert to string (e.g., for objects that aren't JSON-serializable)
    return str(value)

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
            json.dump(_json_safe(tasks_db), f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save tasks to {TASKS_FILE}: {e}")


def persist_task_state(task_id: str):
    """
    Persist a single task state to its own JSON file.

    This provides per-lesson snapshots that can be inspected independently
    from the global tasks.json store.
    """
    task = tasks_db.get(task_id)
    if not task:
        return

    try:
        os.makedirs(TASK_STATE_DIR, exist_ok=True)
        task_file = os.path.join(TASK_STATE_DIR, f"{task_id}.json")
        payload = {
            "task_id": task_id,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            **_json_safe(task),
        }
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to persist task {task_id} state: {e}")

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
    persist_task_state(task_id)

    try:
        initial_state = {
            "user_input": request.topic,
            "topic": "",
            "difficulty": request.current_level,
            "granularity": request.granularity,
            "teacher_gender": request.teacher_gender,
            "sub_topics": [],
            "plans": {},
            "slides": {},
            "intro_text": "",
            "messages": [],
        }

        # Initialize result in tasks_db
        tasks_db[task_id]["result"] = initial_state
        persist_task_state(task_id)

        # Use streaming to get incremental updates from nodes
        async for chunk in planning_graph.astream(initial_state):
            for node_name, state_update in chunk.items():
                if "messages" in state_update:
                    del state_update["messages"]

                # Update the result incrementally
                tasks_db[task_id]["result"].update(state_update)
                logger.info(f"  ⚡ Phase 1: Update from {node_name} for task {task_id}")
                persist_task_state(task_id)

        tasks_db[task_id]["status"] = "planning_completed"
        logger.info(f"Planning for {task_id} completed successfully.")
        save_tasks()
        persist_task_state(task_id)

    except Exception as e:
        logger.error(f"Planning task {task_id} failed: {str(e)}", exc_info=True)
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)
        save_tasks()
        persist_task_state(task_id)


async def run_generation_task(task_id: str, request: ConfirmPlanRequest):
    logger.info(f"Starting full generation task {task_id}")
    tasks_db[task_id]["status"] = "processing"
    save_tasks()
    persist_task_state(task_id)

    try:
        # Resume from the previous state but with confirmed/modified plans
        current_state = tasks_db[task_id]["result"]

        if request.topic:
            current_state["topic"] = request.topic
        if request.sub_topics:
            current_state["sub_topics"] = request.sub_topics

        current_state["plans"] = request.plans
        persist_task_state(task_id)

        # Run Phase 2 (Streaming for incremental updates)
        async for chunk in full_graph.astream(current_state):
            # chunk is {node_name: state_update}
            for node_name, state_update in chunk.items():
                if "messages" in state_update:
                    del state_update["messages"]
                current_result = tasks_db[task_id]["result"]

                _merge_generation_state(current_result, state_update)

                if tasks_db[task_id]["status"] == "processing" and _has_preview_content(current_result):
                    tasks_db[task_id]["status"] = "preview_ready"
                
                logger.info(
                    f"  ⚡ Incremental update from {node_name} for mission {task_id}"
                )
                save_tasks()
                persist_task_state(task_id)

        tasks_db[task_id]["status"] = "completed"
        logger.info(f"Generation for {task_id} completed successfully.")
        save_tasks()
        persist_task_state(task_id)

    except Exception as e:
        logger.error(f"Generation task {task_id} failed: {str(e)}", exc_info=True)
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)
        save_tasks()
        persist_task_state(task_id)


@router.post("/")
async def generate_lesson(
    request: GenerateLessonRequest, background_tasks: BackgroundTasks
):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending"}
    save_tasks()
    persist_task_state(task_id)

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
