from ..llm.model_loader import load_groq, load_groq_fast, load_openai
from ..state import TutorState
import uuid
import json
import ast
import re


def extract_sub_topic(state: TutorState) -> TutorState:
    system_prompt = """You are an AI-powered educational assistant that helps design structured learning content. 
    Your goal is to break down a topic into exactly 1 logical sub-topic for testing.

    CRITICAL RULES:
    1. STICK EXACTLY to the user's topic. Do NOT rephrase it or change its scope.
    2. TOTAL COVERAGE: If the user provides a topic with multiple parts (e.g., "Physical AND Chemical Reactions"), ensure BOTH parts are represented in the sub-topics. Do NOT ignore any part of the user's request.
    3. The sub-topics should be logical segments of the EXACT topic provided.
    4. For each sub-topic, estimate its difficulty level as "Beginner", "Intermediate", or "Advanced".

    Format the output as a valid JSON object like:
    {
        "topic": "<EXACT original topic provided>",
        "sub_topics": [
            {"name": "Sub-topic 1 name", "difficulty": "Beginner"},
            {"name": "Sub-topic 2 name", "difficulty": "Beginner"}
        ]
    }

    If the topic is too vague, respond with: {"sub_topics": []}
    """
    user_prompt = state.get("topic", "")
    llm = load_groq()
    topic = llm.invoke(system_prompt + " " + user_prompt)

    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", topic.content)
    if json_match:
        json_string = json_match.group(1).strip()
    else:
        # Assume the whole content is the JSON string
        json_string = topic.content.strip()
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        print("Error: Model did not return valid JSON")
        print(topic.content)
        state["sub_topics"] = []
        return state

    # Add unique IDs to subtopics and limit to 1 for testing
    sub_topics = data.get("sub_topics", [])[:1]  # Force exactly 1 for testing

    for i, sub in enumerate(sub_topics, start=1):
        sub["id"] = f"sub_{i}_{uuid.uuid4().hex[:6]}"

    state["sub_topics"] = sub_topics
    return state


if __name__ == "__main__":
    State = {"topic": "Computer generations"}
    print(extract_sub_topic(State))
