"""
LangSmith Configuration Module

This module configures LangSmith tracing, monitoring, and evaluation
for the AI Teaching System's LangGraph workflow.

Environment Variables Required:
- LANGCHAIN_TRACING_V2: Set to "true" to enable tracing
- LANGCHAIN_API_KEY: Your LangSmith API key
- LANGCHAIN_PROJECT: Project name for organizing traces
"""

import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from datetime import datetime

# Load environment variables
load_dotenv()


def is_tracing_enabled() -> bool:
    """Check if LangSmith tracing is enabled."""
    return os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"


def get_project_name() -> str:
    """Get the LangSmith project name."""
    return os.getenv("LANGCHAIN_PROJECT", "AI-Teacher-App")


def configure_langsmith():
    """
    Configure LangSmith environment variables.
    This function should be called at application startup.
    """
    if not is_tracing_enabled():
        print(
            "⚠️  LangSmith tracing is disabled. Set LANGCHAIN_TRACING_V2=true to enable."
        )
        return False

    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("⚠️  LANGCHAIN_API_KEY not found in environment variables.")
        return False

    project_name = get_project_name()
    print(f"✓ LangSmith tracing enabled for project: {project_name}")
    return True


def get_run_metadata(
    topic: str = "", difficulty: str = "", run_type: str = "workflow"
) -> Dict[str, Any]:
    """
    Generate custom metadata for LangSmith runs.

    Args:
        topic: The educational topic being processed
        difficulty: Difficulty level (Beginner, Intermediate, Advanced)
        run_type: Type of run (workflow, test, evaluation)

    Returns:
        Dictionary of metadata to attach to LangSmith traces
    """
    metadata = {
        "run_type": run_type,
        "timestamp": datetime.now().isoformat(),
    }

    if topic:
        metadata["topic"] = topic
    if difficulty:
        metadata["difficulty"] = difficulty

    return metadata


def print_trace_url(run_id: Optional[str] = None):
    """
    Print the LangSmith trace URL for a given run.

    Args:
        run_id: The run ID from LangSmith (optional)
    """
    if not is_tracing_enabled():
        return

    project_name = get_project_name()
    base_url = "https://smith.langchain.com"

    if run_id:
        print(
            f"\n🔍 View trace: {base_url}/o/default/projects/p/{project_name}/r/{run_id}"
        )
    else:
        print(f"\n🔍 View all traces: {base_url}/o/default/projects/p/{project_name}")


# Configure on import
configure_langsmith()
