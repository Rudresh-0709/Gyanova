from .node.topic_node import extract_topic
from .node.sub_topic_node import extract_sub_topic
from .node.suggest_topic_node import suggest_sub_topic
from .node.new_slide_planner import slide_planning_node
from .node.blueprint_mapper import blueprint_mapper_node
from .node.narration_node import generate_all_narrations
from .node.intro_narration_node import intro_narration_node
from .state import TutorState

from langgraph.graph import StateGraph, END

graph = StateGraph(TutorState)

graph.add_node("topic_node", extract_topic)
graph.add_node("sub_topic_node", extract_sub_topic)
graph.add_node("slide_planner", slide_planning_node)
graph.add_node("blueprint_mapper", blueprint_mapper_node)
graph.add_node("narration_node", generate_all_narrations)
graph.add_node("intro_narration_node", intro_narration_node)

graph.set_entry_point("topic_node")
graph.add_edge("topic_node", "sub_topic_node")
graph.add_edge("sub_topic_node", "slide_planner")
graph.add_edge("slide_planner", "blueprint_mapper")
graph.add_edge("blueprint_mapper", "narration_node")
graph.add_edge("narration_node", "intro_narration_node")
graph.add_edge("intro_narration_node", END)
