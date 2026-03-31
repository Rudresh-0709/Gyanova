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
import shutil
import time
from urllib.parse import urlparse

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

AUDIO_TTL_SECONDS = int(os.getenv("AUDIO_TTL_SECONDS", "3600"))
ACTIVE_TASK_STATUSES = {"pending", "planning", "planning_completed", "processing"}


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


def _task_state_file(task_id: str) -> str:
    return os.path.join(TASK_STATE_DIR, f"{task_id}.json")


def _collect_audio_paths_from_result(result: Dict[str, Any]) -> List[Path]:
    """Collect absolute audio file paths referenced in a task result payload."""
    if not isinstance(result, dict):
        return []

    paths: List[Path] = []

    def add_audio_path(value: Any):
        if not isinstance(value, str) or not value:
            return

        # Only delete local files; ignore HTTP(S) and unresolved URLs.
        if value.startswith("http://") or value.startswith("https://"):
            return
        if value.startswith("/audio/"):
            rel = value.replace("/audio/", "", 1)
            candidate = DATA_ROOT / "audio_output" / rel
            paths.append(candidate)
            return

        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            return

        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = ROOT_DIR / candidate
        paths.append(candidate)

    lesson_intro = result.get("lesson_intro_narration") or {}
    if isinstance(lesson_intro, dict):
        add_audio_path(lesson_intro.get("audio_url"))
        for seg in lesson_intro.get("narration_segments", []) or []:
            if isinstance(seg, dict):
                add_audio_path(seg.get("audio_url"))

    subtopic_intros = result.get("subtopic_intro_narrations") or {}
    if isinstance(subtopic_intros, dict):
        for intro in subtopic_intros.values():
            if not isinstance(intro, dict):
                continue
            add_audio_path(intro.get("audio_url"))
            for seg in intro.get("narration_segments", []) or []:
                if isinstance(seg, dict):
                    add_audio_path(seg.get("audio_url"))

    slides = result.get("slides") or {}
    if isinstance(slides, dict):
        for slide_list in slides.values():
            if not isinstance(slide_list, list):
                continue
            for slide in slide_list:
                if not isinstance(slide, dict):
                    continue
                add_audio_path(slide.get("audio_url"))
                for seg in slide.get("narration_segments", []) or []:
                    if isinstance(seg, dict):
                        add_audio_path(seg.get("audio_url"))

    # Deduplicate while preserving order
    seen = set()
    deduped: List[Path] = []
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped


def _delete_audio_paths(paths: List[Path]) -> int:
    """Delete files and prune empty parent directories under .persistent_data/audio_output."""
    deleted = 0
    audio_root = (DATA_ROOT / "audio_output").resolve()

    for path in paths:
        try:
            if not path.exists() or not path.is_file():
                continue
            path.unlink()
            deleted += 1

            # Prune empty directories up to audio root.
            current = path.parent
            while current != audio_root and current.exists():
                if any(current.iterdir()):
                    break
                current.rmdir()
                current = current.parent
        except Exception as e:
            logger.warning(f"Failed deleting audio path {path}: {e}")

    return deleted


def cleanup_task_audio(task_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Delete task audio when either:
    - force=True (lesson explicitly closed), or
    - task is non-active and task-state file age >= AUDIO_TTL_SECONDS.
    """
    task = tasks_db.get(task_id)
    if not task:
        return {"task_id": task_id, "deleted": 0, "eligible": False, "reason": "task_not_found"}

    status = str(task.get("status", "")).lower()
    task_file = _task_state_file(task_id)
    now = time.time()
    last_update_ts = os.path.getmtime(task_file) if os.path.exists(task_file) else now
    age_seconds = max(0, int(now - last_update_ts))

    eligible = force or (status not in ACTIVE_TASK_STATUSES and age_seconds >= AUDIO_TTL_SECONDS)
    if not eligible:
        return {
            "task_id": task_id,
            "deleted": 0,
            "eligible": False,
            "reason": "not_due",
            "age_seconds": age_seconds,
            "status": status,
        }

    result = task.get("result") or {}
    paths = _collect_audio_paths_from_result(result)
    deleted = _delete_audio_paths(paths)
    return {
        "task_id": task_id,
        "deleted": deleted,
        "eligible": True,
        "force": force,
        "age_seconds": age_seconds,
        "status": status,
    }


def cleanup_expired_task_audio() -> Dict[str, Any]:
    """Sweep all tasks and delete audio for closed or TTL-expired lessons."""
    total_deleted = 0
    cleaned_tasks = 0
    for task_id in list(tasks_db.keys()):
        info = cleanup_task_audio(task_id, force=False)
        if info.get("eligible"):
            cleaned_tasks += 1
            total_deleted += int(info.get("deleted", 0))

    return {
        "cleaned_tasks": cleaned_tasks,
        "deleted_files": total_deleted,
        "ttl_seconds": AUDIO_TTL_SECONDS,
    }

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
            "unsupported_topic": False,
            "unsupported_subject": "",
            "unsupported_message": "",
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

        if current_state.get("unsupported_topic"):
            tasks_db[task_id]["status"] = "failed"
            tasks_db[task_id]["error"] = current_state.get(
                "unsupported_message",
                "Math-related slides are currently under working. Please try a non-math topic for now.",
            )
            save_tasks()
            persist_task_state(task_id)
            return

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

    result = task.get("result") or {}
    if isinstance(result, dict) and result.get("unsupported_topic"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "unsupported_message",
                "Math-related slides are currently under working. Please try a non-math topic for now.",
            ),
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


@router.post("/{task_id}/close")
async def close_lesson(task_id: str):
    """
    Mark a lesson as closed and delete its audio files immediately.
    """
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    previous_status = task.get("status")
    task["status"] = "closed"

    cleanup_info = cleanup_task_audio(task_id, force=True)
    task.setdefault("meta", {})
    if isinstance(task.get("meta"), dict):
        task["meta"]["audio_cleanup"] = {
            "deleted_files": cleanup_info.get("deleted", 0),
            "closed_at": datetime.utcnow().isoformat() + "Z",
        }

    save_tasks()
    persist_task_state(task_id)

    return {
        "task_id": task_id,
        "previous_status": previous_status,
        "status": "closed",
        "audio_deleted_files": cleanup_info.get("deleted", 0),
    }
