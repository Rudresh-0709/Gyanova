from ..llm.model_loader import load_groq, load_groq_fast, load_openai
from ..state import TutorState
import json


def extract_topic():
    system_prompt = """You are an intelligent assistant that extracts and analyzes educational topics from natural language user input.

        Your task is to:
        1. Identify the EXACT academic topic or concept from the user's input.
        2. CRITICAL: Do NOT rephrase or "clean" the topic into a different name if it is already specific. 
           - If the user says "Physical and Chemical Reactions", the topic MUST be "Physical and Chemical Reactions".
           - Do NOT narrow it down to "Types of Chemical Reactions" or "Mechanisms".
           - If there are multiple related parts (e.g., "A and B"), preserve BOTH.
        3. Estimate the topic's granularity:
            - "Too Broad" (e.g., "Math", "Science")
            - "Focused" (e.g., "Solving Quadratic Equations", "Physical and Chemical Reactions")
            - "Too Narrow" (e.g., "Solving 3x + 2 = 11 using inverse operations")

        Return your response as a JSON object in the following format:
        {
            "topic": "<The EXACT phrased topic from user input>",
            "granularity": "<Too Broad | Focused | Too Narrow>"
        }

        If the input is vague, set topic to "No clear topic detected" and granularity to "N/A".
        Keep the output clean with no extra commentary.
        """

    user_prompt = input("You: ")
    llm = load_groq()
    topic = llm.invoke(system_prompt + " " + user_prompt)
    parsed = json.loads(topic.content)
    extracted_topic = parsed.get("topic", "No clear topic detected")
    extracted_granularity = parsed.get(
        "granularity", "No defined granularity of the subject"
    )
    state = TutorState()
    state.topic = topic.content
    # Yes, you should pass `state` as a parameter if this function is a node in a LangGraph graph.


def extract_topic(state: TutorState) -> TutorState:
    system_prompt = """You are an intelligent assistant that extracts and analyzes educational topics from natural language user input.

        Your task is to:
        1. Identify the EXACT academic topic or concept from the user's input.
        2. CRITICAL: Do NOT rephrase or "clean" the topic into a different name if it is already specific. 
           - If the user says "Physical and Chemical Reactions", the topic MUST be "Physical and Chemical Reactions".
           - If the user says "Assumed Mean", the topic MUST be "Assumed Mean".
           - Do NOT narrow it down to "Types of Chemical Reactions" or "Mechanisms" - preserve the user's exact phrasing.
           - If there are multiple related parts (e.g., "A and B"), preserve BOTH.
        3. Estimate the topic's granularity:
            - "Too Broad" (e.g., "Math", "Science", "Statistics")
            - "Focused" (e.g., "Solving Quadratic Equations", "Physical and Chemical Reactions", "Assumed Mean")
            - "Too Narrow" (e.g., "Solving 3x + 2 = 11 using inverse operations")

        IMPORTANT: Accept ANY single topic or concept as valid, even if it's:
        - Technical/specialized terms (e.g., "Assumed Mean", "Photosynthesis", "Recursion")
        - Compound topics (e.g., "Limits and Continuity")
        - Niche subjects (e.g., "Byzantine Fault Tolerance")
        
        ONLY return "No clear topic detected" if the input is:
        - Completely empty or just punctuation
        - Random gibberish with no semantic meaning
        - Not a single identifiable topic (e.g., "tell me a story" or "how are you")

        Return your response as a JSON object in the following format:
        {
            "topic": "<The EXACT phrased topic from user input>",
            "granularity": "<Too Broad | Focused | Too Narrow>"
        }

        Keep the output clean with no extra commentary.
        """

    user_prompt = state.get("user_input", "")
    llm = load_groq()
    topic = llm.invoke(system_prompt + " " + user_prompt)

    # DEBUG: Show raw topic extraction output
    print("\n--- [DEBUG] TOPIC EXTRACTION LLM OUTPUT ---")
    print(topic.content)
    print("--------------------------------------------\n")

    import re

    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", topic.content)
    if json_match:
        json_string = json_match.group(1).strip()
    else:
        json_string = topic.content.strip()

    try:
        parsed = json.loads(json_string)
    except json.JSONDecodeError:
        # If LLM fails to return JSON, treat the input as-is (most likely a valid topic)
        user_input = state.get("user_input", "").strip()
        if user_input:
            parsed = {"topic": user_input, "granularity": "Focused"}
        else:
            parsed = {"topic": "No clear topic detected", "granularity": "N/A"}

    # ✅ Store clean values in state
    state["topic"] = parsed.get("topic", "No clear topic detected")
    state["granularity"] = parsed.get("granularity", "N/A")

    # Return only modified fields for clean state management
    return {
        "topic": state["topic"],
        "granularity": state["granularity"],
    }
