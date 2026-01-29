"""
LangGraph Workflow for AI Teaching System

Complete Pipeline (MVP - Without Image Generation):
1. Topic Extraction
2. Subtopic Breakdown
3. Slide Planning (pedagogy-first approach)
4. Blueprint Mapping (visual template assignment)
5. Narration Generation (with Wikipedia/Tavily fact-checking)
6. Content Generation (with smart icon selection)
7. Intro Narration

Image Generation: Commented out for MVP (will use Banana.dev/Replicate later)

New Systems Integrated:
- Two-layer fact retrieval (Wikipedia → Tavily)
- Smart icon selection (Groq-based semantic matching)
"""

from .node.topic_node import extract_topic
from .node.sub_topic_node import extract_sub_topic
from .node.suggest_topic_node import suggest_sub_topic
from .node.new_slide_planner import slide_planning_node
from .node.blueprint_mapper import blueprint_mapper_node
from .node.narration_node import generate_all_narrations
from .node.content_generation_node import content_generation_node

# from .node.image_generation_node import image_generation_node  # TODO: Add when image APIs ready
from .node.intro_narration_node import intro_narration_node
from .state import TutorState

from langgraph.graph import StateGraph, END

# Initialize the state graph
graph = StateGraph(TutorState)

# ═══════════════════════════════════════════════════════════════════════════
# NODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

# 1. Topic Analysis
graph.add_node("topic_node", extract_topic)

# 2. Subtopic Breakdown
graph.add_node("sub_topic_node", extract_sub_topic)

# 3. Slide Planning (pedagogy-first)
graph.add_node("slide_planner", slide_planning_node)

# 4. Blueprint Mapping (visual templates)
graph.add_node("blueprint_mapper", blueprint_mapper_node)

# 5. Narration Generation (with fact-checking)
# Uses Wikipedia → Tavily fact retrieval system
graph.add_node("narration_node", generate_all_narrations)

# 6. Content Generation (with smart icon selection)
# Uses Groq LLM to select contextually appropriate RemixIcons
graph.add_node("content_generation_node", content_generation_node)

# 7. Image Generation (DISABLED FOR MVP)
# TODO: Re-enable when Banana.dev/Replicate/other image API is ready
# graph.add_node("image_generation_node", image_generation_node)

# 8. Intro Narration (final step)
graph.add_node("intro_narration_node", intro_narration_node)

# ═══════════════════════════════════════════════════════════════════════════
# WORKFLOW EDGES (Sequential Pipeline)
# ═══════════════════════════════════════════════════════════════════════════

graph.set_entry_point("topic_node")
graph.add_edge("topic_node", "sub_topic_node")
graph.add_edge("sub_topic_node", "slide_planner")
graph.add_edge("slide_planner", "blueprint_mapper")
graph.add_edge("blueprint_mapper", "narration_node")
graph.add_edge("narration_node", "content_generation_node")
# Skip image generation for MVP
# graph.add_edge("content_generation_node", "image_generation_node")
# graph.add_edge("image_generation_node", "intro_narration_node")
graph.add_edge("content_generation_node", "intro_narration_node")  # Direct to intro
graph.add_edge("intro_narration_node", END)

# Compile the graph
compiled_graph = graph.compile()
