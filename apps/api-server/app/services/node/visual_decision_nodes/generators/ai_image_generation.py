import base64
from io import BytesIO

from langchain_google_genai import ChatGoogleGenerativeAI
from ....llm.model_loader import load_gemini_image
from PIL import Image
from langchain_core.messages import HumanMessage
from .domain_tool import classify_domain

import os

def generate_ai_image(prompt, narration, output_path="ai_image.png"):
    """
    Generates an educational AI image using the narration and image prompt.
    Ensures clarity, factual correctness, and simple educational style.
    """
    llm = load_gemini_image()

    # 🧩 Combine narration list into text if needed
    if isinstance(narration, list):
        narration_text = " ".join(narration)
    else:
        narration_text = str(narration or "")

    domain = classify_domain(narration=narration, image_prompt=prompt)
    print(f"🧭 Detected domain: {domain}")

    style_guides = {
        "Science": "Use a clear, educational, labeled, and balanced scientific diagram style.Background: clean, educational (white/neutral), readable fonts. Avoid over-artistic or 3D atomic representations unless explicitly asked.",
        "Technology": "Use a clean, schematic, futuristic visual with modern tones and symmetry.",
        "Mythology": "Use a cinematic, artistic, and divine tone with mythic symbolism.",
        "Finance": "Use minimal, infographic-style visuals with clear iconography and labels.",
        "History": "Use historical illustration with authentic period details and textures.",
        "Other": "Use a visually engaging yet contextually relevant art style.",
    }
    style_prompt = style_guides.get(domain, style_guides["Other"])

    # 🎯 Build a context-aware prompt for Gemini
    full_prompt = (
        f"You are an educational illustrator. Create a clear and accurate image based on the following context.\n\n"
        f"🎓 **Narration Context:** {narration_text}\n"
        f"🖼️ **Image Description:** {prompt}\n"
        f"**Style:** {style_prompt}\n\n"
        f"The image should be easy to understand for students and represent the concept accurately.\n"
        f"Use a clean, labeled, educational visual style — like a textbook diagram or infographic.\n"
        f"Avoid artistic filters, abstract shapes, or unnecessary decorative elements.\n"
        f"Prefer minimal color palette, white background, and balanced composition.\n"
    )

    # 🧠 Invoke Gemini for image generation
    response = llm.invoke(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt}
                ]
            }
        ],
        generation_config={
            "response_modalities": ["TEXT", "IMAGE"]
        }
    )

    # 🖼️ Extract image part
    image_part = next((p for p in response.content if isinstance(p, dict) and "image_url" in p), None)

    if image_part:
        # Decode base64 image
        img_base64 = image_part["image_url"]["url"].split("base64,")[-1]
        img_bytes = base64.b64decode(img_base64)

        # Also save internally (optional safety)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        print(f"✅ AI-generated image saved at {output_path}")

        # Return image bytes for generate_visuals()
        return img_bytes

    else:
        print("❌ Image generation failed. Model response content:")
        print(response.content)
        return None