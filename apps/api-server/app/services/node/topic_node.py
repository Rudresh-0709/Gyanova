from ..llm.model_loader import load_groq,load_groq_fast,load_openai
from ..state import TutorState
import json

def extract_topic():
    system_prompt = (
        """You are an intelligent assistant that extracts and analyzes educational topics from natural language user input.

        Your task is to:
        1. Identify one clear and specific academic topic or concept from the user's input that would be suitable for tutoring.
        2. Estimate the topic's granularity as one of the following levels:
            - "Too Broad" (e.g., "Math", "Science")
            - "Focused" (e.g., "Solving Quadratic Equations", "Photosynthesis")
            - "Too Narrow" (e.g., "Solving 3x + 2 = 11 using inverse operations")

        Return your response as a JSON object in the following format:
        {
            "topic": "<cleaned topic title or 'No clear topic detected'>",
            "granularity": "<Too Broad | Focused | Too Narrow>"
        }

        If the input is vague, off-topic, or lacks an educational concept, set topic to "No clear topic detected" and granularity to "N/A".
        Keep the output clean with no extra commentary.
        """
    )

    user_prompt=input("You: ")
    llm=load_groq()
    topic=llm.invoke(system_prompt+" "+user_prompt)
    parsed = json.loads(topic.content)
    extracted_topic=parsed.get("topic","No clear topic detected")
    extracted_granularity=parsed.get("granularity","No defined granularity of the subject")
    # state.topic=topic.content
    # return state
    print(extracted_topic)
    print(topic)

if __name__ == "__main__":
    extract_topic()