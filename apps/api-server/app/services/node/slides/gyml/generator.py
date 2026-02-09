import json
import os
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

try:
    from ...llm.model_loader import load_openai
except ImportError:
    # Fallback for different import paths
    # Need 5 levels up to reach api-server root from gyml/
    root = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        root = os.path.dirname(root)
    if root not in sys.path:
        sys.path.append(root)
    from app.services.llm.model_loader import load_openai


class GyMLContentGenerator:
    """
    Standalone utility to generate GyML-compliant slide content using LLMs.
    """

    def __init__(self):
        self.llm = load_openai()
        self.schema = self._load_schema()

    def _load_schema(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "llm_schema.json")
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading schema: {e}")
            return "{}"

    def generate(
        self,
        narration: str,
        title: str,
        purpose: str,
        subtopic: str,
        hint: str = "",
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Generate structured GyML content from narration.
        """
        prompt = f"""
        You are an expert educational content designer.
        Your task is to convert the Teacher's Narration into a structured visual slide using GyML (Gyanova Markup Language).

        SLIDE CONTEXT:
        - Title: {title}
        - Purpose: {purpose}
        - Subtopic: {subtopic}
        - Narration: {narration}
        
        {f"📚 ADDITIONAL CONTEXT:\\n{context}" if context else ""}

        INSTRUCTIONS:
        1. Analyze the narration to determine the best 'intent' and 'contentBlocks'.
        2. 💎 RICHNESS REQUIREMENT (CRITICAL):
           - A slide MUST have high information density. Aim for 3-4 distinct content blocks.
           - Use semantic paragraph types for structure:
             * 'intro_paragraph': To set the stage.
             * 'context_paragraph': For background or history.
             * 'annotation_paragraph': For side notes or tips.
             * 'outro_paragraph': For summaries or final thoughts.
             * 'caption': For figure descriptions.
           - Use 'smart_layout' for the main visualization (Timeline, Table, Code, Card Grid, etc.).
           
        3. FORMATTING RULES:
           - Use 'ri-*' icon names for icons (RemixIcon).
           - Ensure 'intent' is one of: introduce, explain, narrate, compare, list, prove, summarize, teach, demo.
           - Choose the most appropriate 'variant' for 'smart_layout'.

        STRICT OUTPUT SCHEMA (JSON ONLY):
        {self.llm_schema_placeholder if hasattr(self, 'llm_schema_placeholder') else self.schema}

        OUTPUT FORMAT:
        Output ONLY the valid JSON object. No preamble or explanation.
        """

        response = self.llm.invoke([{"role": "user", "content": prompt}])
        content = response.content.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw content: {content}")
            return {
                "title": title,
                "intent": "explain",
                "contentBlocks": [
                    {
                        "type": "paragraph",
                        "text": "Generation failed. Please check logs.",
                    }
                ],
            }


if __name__ == "__main__":
    # Test generation
    generator = GyMLContentGenerator()
    test_narration = "In 2010, the company was founded in a small garage. By 2015, we reached 1 million users. Today, we are a global leader in AI education."
    result = generator.generate(
        narration=test_narration,
        title="Our Growth Journey",
        purpose="narrate",
        subtopic="Company History",
    )
    print(json.dumps(result, indent=2))
