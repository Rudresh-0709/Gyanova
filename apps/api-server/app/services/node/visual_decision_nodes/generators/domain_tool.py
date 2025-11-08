from ....llm.model_loader import load_gemini_image, load_groq_fast
from groq import Groq
from langchain_core.messages import HumanMessage

def classify_domain(narration: str, image_prompt: str) -> str:
    """
    Classifies the most relevant domain for an image prompt based on narration context.
    """
    llm = load_groq_fast()

    combined_text = f"""
    Narration: {narration}
    Image Description: {image_prompt}

    Based on this, choose the single most relevant domain from the following:
    - Science
    - History
    - Mythology
    - Technology
    - Art/Design
    - General Knowledge
    - Geography
    - Other (if none of the above fit)
    
    Respond ONLY with the domain name.
    """

    response = llm.invoke([HumanMessage(content=combined_text)])
    domain = response.content.strip().lower()

    # Normalize response to consistent label
    valid_domains = {
        "science",
        "history",
        "mythology",
        "technology",
        "art/design",
        "general knowledge",
        "geography",
        "other",
    }
    for d in valid_domains:
        if d in domain:
            return d.capitalize()

    return "Other"
