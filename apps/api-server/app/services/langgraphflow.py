"""
LangGraph Workflow for AI Teaching System (GyML-First)

Complete Pipeline:
1. Topic Extraction
2. Subtopic Breakdown
3. Slide JSON Generator (Planning + Rich Content + Narration + GyML)
4. Intro Narration
5. Rendering (GyML -> HTML)

New Systems Integrated:
- Two-layer fact retrieval (Wikipedia → Tavily)
- Smart icon selection (Groq-based semantic matching)
- LangSmith tracing and monitoring (automatic)
"""

# Import LangSmith configuration (enables automatic tracing)
from .langsmith_config import configure_langsmith

from .node.topic_node import extract_topic
from .node.sub_topic_node import extract_sub_topic
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

# 3. Slide JSON Generator (Planning + Rich Content + Narration + GyML)
# Uses GyMLContentGenerator for high visual density
graph.add_node("content_generation_node", content_generation_node)

# 4. Intro Narration (final step)
graph.add_node("intro_narration_node", intro_narration_node)

# 9. Rendering (GyML -> HTML)
from .node.rendering_node import rendering_node

graph.add_node("rendering_node", rendering_node)

# ═══════════════════════════════════════════════════════════════════════════
# WORKFLOW EDGES (Sequential Pipeline)
# ═══════════════════════════════════════════════════════════════════════════

graph.set_entry_point("topic_node")
graph.add_edge("topic_node", "sub_topic_node")
graph.add_edge("sub_topic_node", "content_generation_node")
graph.add_edge("content_generation_node", "intro_narration_node")  # Direct to intro
graph.add_edge("intro_narration_node", "rendering_node")
graph.add_edge("rendering_node", END)

# Compile the graph
compiled_graph = graph.compile()
