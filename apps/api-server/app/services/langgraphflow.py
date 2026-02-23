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

# Import LangSmith configuration (enables automatic tracing)
from .langsmith_config import configure_langsmith

from .node.topic_node import extract_topic
from .node.sub_topic_node import extract_sub_topic
from .node.lesson_planning_node import lesson_planning_node
from .node.content_generation_node import content_generation_node
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

planning_builder.set_entry_point("topic_node")
planning_builder.add_edge("topic_node", "sub_topic_node")
planning_builder.add_edge("sub_topic_node", "planning_node")
planning_builder.add_edge("planning_node", END)

planning_graph = planning_builder.compile()

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
full_builder.add_edge("intro_narration_node", "rendering_node")
full_builder.add_edge("rendering_node", "audio_generation_node")

# Routing logic after audio generation
full_builder.add_conditional_edges(
    "audio_generation_node",
    should_continue,
    {"continue": "content_generation_node", "end": END},
)

full_graph = full_builder.compile()

# Legacy alias for backward compatibility
compiled_graph = full_graph
