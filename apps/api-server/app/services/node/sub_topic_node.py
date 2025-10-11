from ..llm.model_loader import load_groq,load_groq_fast,load_openai
from ..state import TutorState
import uuid
import json
import ast

def extract_sub_topic(state:TutorState)->TutorState:
    system_prompt = (
    """You are an AI-powered educational assistant that helps design structured learning content. 
    Given a topic, break it down into 3 to 7 essential sub-topics suitable for tutoring or lesson planning. 
    Each sub-topic should be distinct, logically ordered, and relevant to building a full understanding of the topic.

    For each sub-topic, also estimate its difficulty level as "Beginner", "Intermediate", or "Advanced" based on 
    how much prior knowledge is typically required.

    Format the output as a valid JSON object like:
    {
        "topic": "<original topic>",
        "sub_topics": [
            {"name": "Sub-topic name", "difficulty": "Beginner"},
            ...
        ]
    }

    If the topic is too vague, non-educational, or not suitable for breakdown, respond with: {"sub_topics": []}
    """
)
    user_prompt=state.get("topic","")
    llm=load_groq()
    topic=llm.invoke(system_prompt+" "+user_prompt)
    try:
        data = json.loads(topic.content)  
    except json.JSONDecodeError:
        print("Error: Model did not return valid JSON")
        state["sub_topics"]=[]
        return state
    
    # Add unique IDs to subtopics
    for i, sub in enumerate(data.get("sub_topics", []), start=1):
        sub["id"] = f"sub_{i}_{uuid.uuid4().hex[:6]}"

    state["sub_topics"]=data.get("sub_topics",[])
    return state