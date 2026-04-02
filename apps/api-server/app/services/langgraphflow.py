"""
LangGraph Workflow for AI Teaching System (GyML-First)

Complete Pipeline:
1. Topic Extraction
2. Subtopic Breakdown
3. Slide JSON Generator (Planning + Rich Content + Narration + GyML)
4. Intro Narration (Lesson and Subtopic intros)
5. Rendering (GyML -> HTML)
6. Audio Generation (OpenAI TTS)
"""

import os

# Import LangSmith configuration (enables automatic tracing)
from .langsmith_config import configure_langsmith

from .node.topic_node import extract_topic
from .node.sub_topic_node import extract_sub_topic
from .node.lesson_planning_node import lesson_planning_node
from .node.content_generation_node import content_generation_node
from .node.teacher_slide_planning_node import teacher_slide_planning_node
from .node.designer_slide_planning_node import designer_slide_planning_node
from .node.coverage_checker_node import coverage_checker_node
from .node.content_generation_v2_node import content_generation_v2_node
from .node.intro_narration_node import intro_narration_node
from .node.rendering_node import rendering_node
from .node.audio_generation_node import audio_generation_node
from .state import TutorState

from langgraph.graph import StateGraph, END

# Phase 1 Graph: Just for Planning
planning_builder = StateGraph(TutorState)
planning_builder.add_node("topic_node", extract_topic)
planning_builder.add_node("sub_topic_node", extract_sub_topic)
planning_builder.add_node("planning_node", lesson_planning_node)


def should_continue_planning(state: TutorState):
    """Router: check if all subtopics have slide plans."""
    sub_topics = state.get("sub_topics", [])
    plans = state.get("plans", {})

    if not sub_topics:
        return "end"

    for sub in sub_topics:
        if sub["id"] not in plans:
            return "continue"
    return "end"


planning_builder.set_entry_point("topic_node")
planning_builder.add_edge("topic_node", "sub_topic_node")
planning_builder.add_edge("sub_topic_node", "planning_node")

planning_builder.add_conditional_edges(
    "planning_node",
    should_continue_planning,
    {"continue": "planning_node", "end": END},
)

planning_graph_v1 = planning_builder.compile()

# Phase 2 Graph: Full Generation (Incremental Subtopic Loop)
full_builder = StateGraph(TutorState)

# Add all nodes
full_builder.add_node("topic_node", extract_topic)
full_builder.add_node("sub_topic_node", extract_sub_topic)
full_builder.add_node("planning_node", lesson_planning_node)
full_builder.add_node("content_generation_node", content_generation_node)
full_builder.add_node("intro_narration_node", intro_narration_node)
full_builder.add_node("rendering_node", rendering_node)
full_builder.add_node("audio_generation_node", audio_generation_node)


def join_node(state: TutorState):
    """Synchronization point for parallel nodes."""
    return state


full_builder.add_node("join_node", join_node)


def should_continue(state: TutorState):
    """Router: check if there are still slides left to generate."""
    sub_topics = state.get("sub_topics", [])
    plans = state.get("plans", {})
    slides = state.get("slides", {})

    for sub in sub_topics:
        sub_id = sub["id"]
        planned_count = len(plans.get(sub_id, []))
        generated_count = len(slides.get(sub_id, []))
        if generated_count < planned_count:
            return "continue"
        # Also check if any slide still lacks audio
        for slide in slides.get(sub_id, []):
            if not slide.get("narration_segments"):
                return "continue"
    return "end"


# Workflow definition
full_builder.set_entry_point("content_generation_node")
full_builder.add_edge("content_generation_node", "intro_narration_node")

# Sequential flow for better stability and state consistency
full_builder.add_edge("intro_narration_node", "rendering_node")
full_builder.add_edge("rendering_node", "audio_generation_node")
full_builder.add_edge("audio_generation_node", "join_node")

# Routing logic after joining
full_builder.add_conditional_edges(
    "join_node",
    should_continue,
    {"continue": "content_generation_node", "end": END},
)

# Compile baseline graph (v1)
full_graph_v1 = full_builder.compile()


# ─────────────────────────────────────────────────────────────────────
# Experimental V2 Graphs (Teacher-first + Designer-first planning)
# ─────────────────────────────────────────────────────────────────────

# V2 Planning Graph
planning_builder_v2 = StateGraph(TutorState)
planning_builder_v2.add_node("topic_node", extract_topic)
planning_builder_v2.add_node("sub_topic_node", extract_sub_topic)
planning_builder_v2.add_node("teacher_planning_node", teacher_slide_planning_node)
planning_builder_v2.add_node("designer_planning_node", designer_slide_planning_node)
planning_builder_v2.add_node("coverage_checker_node", coverage_checker_node)

planning_builder_v2.set_entry_point("topic_node")
planning_builder_v2.add_edge("topic_node", "sub_topic_node")
planning_builder_v2.add_edge("sub_topic_node", "teacher_planning_node")
planning_builder_v2.add_edge("teacher_planning_node", "designer_planning_node")
planning_builder_v2.add_edge("designer_planning_node", "coverage_checker_node")
planning_builder_v2.add_conditional_edges(
    "coverage_checker_node",
    should_continue_planning,
    {"continue": "teacher_planning_node", "end": END},
)

planning_graph_v2 = planning_builder_v2.compile()

# V2 Full Generation Graph
full_builder_v2 = StateGraph(TutorState)
full_builder_v2.add_node("topic_node", extract_topic)
full_builder_v2.add_node("sub_topic_node", extract_sub_topic)
full_builder_v2.add_node("teacher_planning_node", teacher_slide_planning_node)
full_builder_v2.add_node("designer_planning_node", designer_slide_planning_node)
full_builder_v2.add_node("content_generation_v2_node", content_generation_v2_node)
full_builder_v2.add_node("intro_narration_node", intro_narration_node)
full_builder_v2.add_node("rendering_node", rendering_node)
full_builder_v2.add_node("audio_generation_node", audio_generation_node)
full_builder_v2.add_node("join_node", join_node)

full_builder_v2.set_entry_point("content_generation_v2_node")
full_builder_v2.add_edge("content_generation_v2_node", "intro_narration_node")
full_builder_v2.add_edge("intro_narration_node", "rendering_node")
full_builder_v2.add_edge("rendering_node", "audio_generation_node")
full_builder_v2.add_edge("audio_generation_node", "join_node")
full_builder_v2.add_conditional_edges(
    "join_node",
    should_continue,
    {"continue": "content_generation_v2_node", "end": END},
)

full_graph_v2 = full_builder_v2.compile()


# Runtime graph selection for safe testing
# Set SLIDE_WORKFLOW_VERSION=v2 to test new workflow through existing API/frontend.
_workflow_version = os.getenv("SLIDE_WORKFLOW_VERSION", "v1").strip().lower()
if _workflow_version == "v2":
    planning_graph = planning_graph_v2
    full_graph = full_graph_v2
else:
    planning_graph = planning_graph_v1
    full_graph = full_graph_v1

# Legacy alias for backward compatibility
compiled_graph = full_graph
