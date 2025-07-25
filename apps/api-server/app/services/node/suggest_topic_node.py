from ..llm.model_loader import load_groq,load_groq_fast,load_openai
from ..state import TutorState
import ast

def suggest_sub_topic():
    system_prompt = (
    """You are an AI teaching assistant that analyzes a given academic topic and determines if it is too broad or too narrow for direct tutoring.

        Your tasks are:
        1. If the topic is too broad (e.g., "Math", "Biology") or too narrow (e.g., "Solving 3x + 2 = 11 using inverse operations"), generate 3 to 7 alternative sub-topics that are more appropriate for structured learning.
        2. Each suggestion should include a difficulty level: "Beginner", "Intermediate", or "Advanced".
        3. If the topic is already well-focused and suitable for tutoring, return: {"sub_topics": []}

        The output must be a **valid JSON object** in this format:

        {
        "topic": "<original topic>",
        "sub_topics": [
            { "name": "<refined sub-topic name>", "difficulty": "<Beginner | Intermediate | Advanced>" },
            ...
        ]
        }

        If the input is vague, off-topic, or unsuitable, return:
        {
        "topic": "<original topic>",
        "sub_topics": []
        }

    """
)
    user_prompt=input("You :")
    llm=load_groq()
    topic=llm.invoke(system_prompt+" "+user_prompt)
    print(topic.content)

if __name__ == "__main__":
    suggest_sub_topic()