from .node.topic_node import extract_topic
from .node.sub_topic_node import extract_sub_topic
from .node.suggest_topic_node import suggest_sub_topic
from state import TutorState

from langgraph.graph import StateGraph, END

graph=StateGraph(TutorState)



graph.set_entry_point()