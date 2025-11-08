import os
import base64
import requests
import traceback
import re
from dotenv import load_dotenv
from ....llm.model_loader import load_gemini_image
from groq import Groq
from .ai_image_generation import generate_ai_image
from .domain_tool import classify_domain

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
cse_id = os.getenv("GOOGLE_CSE_ID")


# ✅ Step 1: Google CSE Image Search
def google_image_search(query, num_images=1):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": cse_id,
        "key": api_key,
        "searchType": "image",
        "num": num_images,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "items" not in data:
        print("❌ No image results found.")
        return []

    return [item["link"] for item in data["items"][:num_images]]


def sanitize_filename(name: str) -> str:
    """
    Convert slide titles to safe filenames.
    Removes special characters and replaces spaces with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip())

import requests
import json


def analyze_cse_image(
    image_url, topic_prompt, model="meta-llama/llama-4-maverick-17b-128e-instruct"
):
    """
    Uses the Llama 4 Maverick Vision model to analyze a CSE image and extract key educational details.
    Returns a structured JSON describing visuals, text, key_details, and visual_change suggestions.
    """

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY)

    # 🧾 Prompt for model — designed as teacher guidance
    system_prompt = (
        "You are an educational visual reviewer and teacher, analyzing an image to decide how it should be reused or recreated for teaching purposes. "
        "Your goal is to identify which elements in the image are essential to preserve for accuracy and learning, and whether this image is suitable for direct educational use. "
        "Evaluate clarity, factual correctness, and visual simplicity for student understanding. "
        "If the image is overly technical, dense, or copyrighted-looking, recommend recreating it using AI or a simple diagram instead. "
        "Describe the visuals, text, and logical relationships that must remain correct if recreated, but also specify what can be simplified or redesigned for better educational clarity. "
        "Finally, classify the image as either 'fit_for_learning' (True/False) and suggest whether to generate a new AI image or chart/diagram. "
        "Output strictly in JSON with fields: visuals, text, key_details, relationships, visual_change, fit_for_learning, issues, and recommendation."
    )

    user_prompt = (
        f"Review the provided image about '{topic_prompt}'. "
        "You are a teacher evaluating whether this visual is suitable for classroom or student learning use. "
        "Identify the most important visual and textual elements that must remain accurate if recreated, including labels, structures, or sequences. "
        "Then, assess whether the image is educationally appropriate — is it clear, simple, and student-friendly? "
        "If it is too complex, cluttered, research-heavy, or may pose copyright issues, suggest that a new image or diagram be generated instead. "
        "Also suggest what can be simplified or restructured for clarity (e.g., using a timeline, flow diagram, or labeled vector art). "
        "Give output strictly in JSON format with the following fields:\n\n"
        "{\n"
        '  "visuals": ["list of key visual elements that must be preserved"],\n'
        '  "text": ["important textual labels or terms to retain"],\n'
        '  "key_details": ["scientific, chronological, or conceptual facts that must stay accurate"],\n'
        '  "relationships": ["how elements connect or flow logically"],\n'
        '  "visual_change": ["ideas for simplification or new formats to make it clearer or more unique"],\n'
        '  "fit_for_learning": true/false,\n'
        '  "issues": ["clarity issue", "too much text", "research figure", "copyright risk"],\n'
        '  "recommendation": "use_as_reference" or "regenerate_ai_image" or "use_chart_diagram"\n'
        "}"
    )
    print(type(image_url), image_url)
    image_url = str(image_url)
    user_prompt = str(user_prompt)
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            # Groq expects a simple string for content + top-level images list
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],  # 👈 correct multimodal key
        },
    ]

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=messages,
        temperature=0.4,
        max_completion_tokens=1024,
        top_p=1,
    )

    # 🧾 Extract full response text
    response_text = completion.choices[0].message.content.strip()

    # 🧩 Parse JSON safely
    try:
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "")
        parsed = json.loads(response_text)
    except Exception as e:
        print("⚠️ JSON parsing error:", e)
        print("Raw output:", response_text)
        parsed = {"visuals": {}, "text": {}, "key_details": {}, "visual_change": {}}

    print("✅ Extracted Educational Blueprint:")
    print(json.dumps(parsed, indent=2))
    return parsed


def generate_ai_enhanced_image(
    prompt,
    narration=None,
    reference_image_url=None,
    image_analysis=None,
    output_path="ai_enhanced_image.png",
):
    """
    Generates an AI-enhanced image using Gemini, optionally with a narration and reference image.
    Supports both local and URL-based reference images.
    """
    llm = load_gemini_image()

    # 🧠 Detect domain for better visual style adaptation
    domain = classify_domain(narration=narration, image_prompt=prompt)
    print(f"🧭 Detected domain: {domain}")

    # 🎨 Choose visual style based on domain
    style_guides = {
        "Science": "Use a clear, educational, labeled, and balanced scientific diagram style.Background: clean, educational (white/neutral), readable fonts. Avoid over-artistic or 3D atomic representations unless explicitly asked.",
        "Technology": "Use a clean, schematic, futuristic visual with modern tones and symmetry.",
        "Mythology": "Use a cinematic, artistic, and divine tone with mythic symbolism.",
        "Finance": "Use minimal, infographic-style visuals with clear iconography and labels.",
        "History": "Use historical illustration with authentic period details and textures.",
        "Other": "Use a visually engaging yet contextually relevant art style.",
    }
    style_prompt = style_guides.get(domain, style_guides["Other"])

    # 🧩 Combine prompts
    full_prompt = f"""
    Image Analysis: {image_analysis}
    Visual topic: {prompt}
    Style: {style_prompt}
    Important factual constraints (non-negotiable):
    {json.dumps(image_analysis.get('key_details', []), indent=2)}

    Layout and relationships:
    {json.dumps(image_analysis.get('relationships', []), indent=2)}

    Text that must appear exactly:
    {json.dumps(image_analysis.get('text', []), indent=2)}

    Visual requirements:
    {json.dumps(image_analysis.get('visuals', []), indent=2)}

    Visual improvements (optional creative ideas):
    {json.dumps(image_analysis.get('visual_change', []), indent=2)}
    "Ensure the image is fully unique and AI-generated, avoid copyright by changing art style or any logos, watermarks, texts if present."
    """

    # 🖼️ Handle reference image (URL or local)
    reference_content = []
    if reference_image_url:
        if os.path.exists(reference_image_url):  # Local → Base64
            with open(reference_image_url, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
            reference_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                }
            )
        else:
            reference_content.append(
                {"type": "image_url", "image_url": {"url": reference_image_url}}
            )
        print(f"🎨 Using reference image: {reference_image_url}")

    # 🧠 Prepare request for Gemini
    content = [
        {
            "role": "user",
            "content": [{"type": "text", "text": full_prompt}, *reference_content],
        }
    ]

    # 🚀 Invoke Gemini model
    response = llm.invoke(
        content, generation_config={"response_modalities": ["TEXT", "IMAGE"]}
    )

    # 🖼️ Extract and save image
    image_part = next(
        (p for p in response.content if isinstance(p, dict) and "image_url" in p), None
    )
    if not image_part:
        print("❌ No image found in Gemini response.")
        print(response.content)
        return None

    img_base64 = image_part["image_url"]["url"].split("base64,")[-1]
    img_bytes = base64.b64decode(img_base64)

    # ✅ Save locally
    with open(output_path, "wb") as f:
        f.write(img_bytes)
    print(f"✅ AI-enhanced image saved as {output_path}")

    return img_bytes


def create_ai_enhanced_visual(
    image_prompt, narration=None, save_dir="generated_images", output_path=None
):
    """
    Searches Google for a reference image, enhances it with Gemini,
    and returns the final saved image path.
    """
    os.makedirs(save_dir, exist_ok=True)

    # 1️⃣ Find base image from Google
    base_images = google_image_search(image_prompt, num_images=1)
    reference_image_url = base_images[0] if base_images else None

    try:
        if reference_image_url:
            image_analysis = analyze_cse_image(reference_image_url, image_prompt)
            recommendation = image_analysis.get("recommendation", "").lower()
        else:
            recommendation = "regenerate_ai_image"

    except Exception as e:
        print("❌ Vision model failed or timed out.")
        print("Error details:", str(e))
        traceback.print_exc()
        # Safe fallback to simple AI generation
        recommendation = "regenerate_ai_image"

    # 2️⃣ Generate enhanced image with narration included
    if not output_path:
        safe_name = sanitize_filename(image_prompt[:50]) + "_enhanced.png"
        output_path = os.path.join(save_dir, safe_name)
    if recommendation == "use_as_reference":
        print("✅ Using reference image for AI enhancement.")
        image_bytes = generate_ai_enhanced_image(
            prompt=image_prompt,
            image_analysis=image_analysis,
            narration=narration,
            reference_image_url=reference_image_url,
            output_path=output_path,
        )

    elif recommendation == "regenerate_ai_image":
        print("🚀 Reference image not suitable. Generating new AI image from prompt.")
        image_bytes = generate_ai_image(
            prompt=image_prompt,
            narration=narration,
            output_path=output_path,
        )

    return image_bytes


# ✅ Example usage
if __name__ == "__main__":
    narration_points = [
        "Early computers used vacuum tubes for processing data in the 1940s.",
        "ENIAC, the first electronic general-purpose computer, was a key innovation.",
        "These computers were huge in size, consumed massive amounts of power, and generated a lot of heat.",
    ]

    narration_text = "\n".join(
        [f"{i+1}. {point}" for i, point in enumerate(narration_points)]
    )
    prompt = "detailed labeled diagram illustrating the internal components of a first-generation computer with vacuum tubes, highlighting ENIAC as the first general-purpose electronic computer, technical and precise educational illustration",
    final_image = create_ai_enhanced_visual(
        image_prompt=prompt, narration=narration_text
    )
    print(f"\nFinal Image Path: {final_image}")
