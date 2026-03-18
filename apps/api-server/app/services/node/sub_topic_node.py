from ..llm.model_loader import load_groq, load_groq_fast, load_openai
from ..state import TutorState
import uuid
import json
import ast
import re


def extract_sub_topic(state: TutorState) -> TutorState:
    system_prompt = """You are an AI-powered educational assistant that helps design structured learning content. 
    Your goal is to break down a topic into logical, technical sub-topics.
    
    CRITICAL RULES:
    1. STICK EXACTLY to the user's topic. Do NOT rephrase it or change its scope.
    2. TECHNICAL DEPTH: Sub-topics should be specific enough to cover laws, mechanisms, and examples (e.g., "Refractive Index & Snell's Law" instead of just "Math").
    3. TOTAL COVERAGE: Ensure all core concepts of the topic are represented in the sub-topics.
    4. For each sub-topic, estimate its difficulty level.

    Format the output as a valid JSON object like:
    {
        "topic": "<EXACT original topic provided>",
        "sub_topics": [
            {"name": "Sub-topic 1 name", "difficulty": "Beginner"},
            {"name": "Sub-topic 2 name", "difficulty": "Intermediate"}
        ]
    }

    If the topic is too vague or invalid (like "No clear topic detected"), respond with: {"sub_topics": []}
    """
    user_prompt = state.get("topic", "")
    
    # Guard: if topic extraction failed, skip sub-topic extraction
    if not user_prompt or user_prompt == "No clear topic detected":
        print("\n⚠️  [WARNING] Skipping sub-topic extraction - topic is invalid")
        state["sub_topics"] = []
        return state
    
    llm = load_groq()
    topic = llm.invoke(system_prompt + " " + user_prompt)

    # DEBUG: Show raw sub-topic output
    print("\n--- [DEBUG] SUB-TOPIC EXTRACTION LLM OUTPUT ---")
    print(topic.content)
    print("------------------------------------------------\n")

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

    # Limit to 1 subtopic for faster testing (as requested)
    sub_topics = data.get("sub_topics", [])[:1]

    for i, sub in enumerate(sub_topics, start=1):
        sub["id"] = f"sub_{i}_{uuid.uuid4().hex[:6]}"

    state["sub_topics"] = sub_topics
    
    # Return only modified fields for clean state management
    return {"sub_topics": state["sub_topics"]}


if __name__ == "__main__":
    State = {"topic": "Computer generations"}
    print(extract_sub_topic(State))
