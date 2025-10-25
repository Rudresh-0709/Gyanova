import os
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from ....llm.model_loader import load_gemini_image, load_groq_fast

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
        "num": num_images
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if "items" not in data:
        print("❌ No image results found.")
        return []
    
    return [item["link"] for item in data["items"][:num_images]]

# ✅ Step 2: Load Gemini Image Model

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
        "science", "history", "mythology", "technology", 
        "art/design", "general knowledge", "geography", "other"
    }
    for d in valid_domains:
        if d in domain:
            return d.capitalize()
    
    return "Other"

# ✅ Step 3: Generate AI-Enhanced Image
# def generate_ai_enhanced_image(prompt, narration=None, reference_image_url=None, output_path="ai_enhanced_image.png"):
#     llm = load_gemini_image()

    
#     domain = classify_domain(narration,prompt)
#     print(f"🧭 Detected domain: {domain}")

#     # 🎨 Choose style based on domain
#     style_guides = {
#         "Science": "Use a clear, educational, labeled, and balanced scientific diagram style.",
#         "Technology": "Use a clean, schematic, futuristic visual with modern tones and symmetry.",
#         "Mythology": "Use a cinematic, artistic, and divine tone with mythic symbolism.",
#         "Finance": "Use minimal, infographic-style visuals with clear iconography and labels.",
#         "History": "Use historical illustration with authentic period details and textures.",
#         "Other": "Use a visually engaging yet contextually relevant art style."
#     }
#     style_prompt = style_guides.get(domain, style_guides["Other"])

#     # 🧩 Combine all prompts
#     full_prompt = f"""
#     Context: {narration or "No narration provided."}
#     Topic: {prompt}
#     Visual Style: {style_prompt}
#     Generate a high-quality AI-enhanced illustration that aligns with the above.
#     """

#     # 🖼️ Handle reference image (URL or local)
#     reference_content = []
#     if reference_image_url:
#         if os.path.exists(reference_image_url):  # Local file → encode to base64
#             with open(reference_image_url, "rb") as img_file:
#                 img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
#             reference_content.append({
#                 "type": "image_url",
#                 "image_url": {"url": f"data:image/png;base64,{img_base64}"}
#             })
#         else:
#             # Assume it's already a valid URL
#             reference_content.append({
#                 "type": "image_url",
#                 "image_url": {"url": reference_image_url}
#             })
#         print(f"🎨 Using reference image: {reference_image_url}")

#     # 🧠 Create request content
#     content = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": full_prompt},
#                 *reference_content
#             ]
#         }
#     ]

#     # 🚀 Generate the image
#     response = llm.invoke(
#         content,
#         generation_config={"response_modalities": ["TEXT", "IMAGE"]}
#     )

#     # 🖼️ Extract the image from response
#     image_part = next((p for p in response.content if isinstance(p, dict) and "image_url" in p), None)
#     if not image_part:
#         print("❌ No image found in Gemini response.")
#         print(response.content)
#         return None

#     # Decode base64 from Gemini output
#     img_base64 = image_part["image_url"]["url"].split("base64,")[-1]
#     img = Image.open(BytesIO(base64.b64decode(img_base64)))
#     img.save(output_path)

#     print(f"✅ AI-enhanced image saved as {output_path}")
#     return output_path

# # ✅ Step 4: Combined Function
# def create_ai_enhanced_visual(image_prompt, save_dir="generated_images"):
#     os.makedirs(save_dir, exist_ok=True)

#     # 1️⃣ Search Google for a base image
#     base_images = google_image_search(image_prompt, num_images=1)
#     reference_image_url = base_images[0] if base_images else None

#     # 2️⃣ Generate AI-enhanced version
#     output_path = os.path.join(save_dir, "enhanced_image.png")
#     final_path = generate_ai_enhanced_image(image_prompt, reference_image_url, output_path)
    
#     return final_path

# # ✅ Step 5: Example Usage
# if __name__ == "__main__":
#     prompt = "illustration showing different atoms with nucleus and orbiting electrons"
#     final_image = create_ai_enhanced_visual(prompt)
#     print(f"\nFinal Image Path: {final_image}")

def generate_ai_enhanced_image(prompt, narration=None, reference_image_url=None, output_path="ai_enhanced_image.png"):
    """
    Generates an AI-enhanced image using Gemini, optionally with a narration and reference image.
    Supports both local and URL-based reference images.
    """
    llm = load_gemini_image()

    # 🧠 Detect domain for better visual style adaptation
    domain = classify_domain(narration=narration,image_prompt=prompt)
    print(f"🧭 Detected domain: {domain}")

    # 🎨 Choose visual style based on domain
    style_guides = {
        "Science": "Use a clear, educational, labeled, and balanced scientific diagram style.",
        "Technology": "Use a clean, schematic, futuristic visual with modern tones and symmetry.",
        "Mythology": "Use a cinematic, artistic, and divine tone with mythic symbolism.",
        "Finance": "Use minimal, infographic-style visuals with clear iconography and labels.",
        "History": "Use historical illustration with authentic period details and textures.",
        "Other": "Use a visually engaging yet contextually relevant art style."
    }
    style_prompt = style_guides.get(domain, style_guides["Other"])

    # 🧩 Combine prompts
    full_prompt = f"""
    Context (from narration): {narration or "No narration provided."}
    Visual topic: {prompt}
    Style: {style_prompt}
    "Use the following image only as a conceptual reference. "
    "Create a new composition with different structure, perspective, and colors. "
    "Do not copy or trace elements directly. "
    "Ensure the image is fully unique and AI-generated."
    """

    # 🖼️ Handle reference image (URL or local)
    reference_content = []
    if reference_image_url:
        if os.path.exists(reference_image_url):  # Local → Base64
            with open(reference_image_url, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
            reference_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            })
        else:
            reference_content.append({
                "type": "image_url",
                "image_url": {"url": reference_image_url}
            })
        print(f"🎨 Using reference image: {reference_image_url}")

    # 🧠 Prepare request for Gemini
    content = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": full_prompt},
                *reference_content
            ]
        }
    ]

    # 🚀 Invoke Gemini model
    response = llm.invoke(content, generation_config={"response_modalities": ["TEXT", "IMAGE"]})

    # 🖼️ Extract and save image
    image_part = next((p for p in response.content if isinstance(p, dict) and "image_url" in p), None)
    if not image_part:
        print("❌ No image found in Gemini response.")
        print(response.content)
        return None

    img_base64 = image_part["image_url"]["url"].split("base64,")[-1]
    img = Image.open(BytesIO(base64.b64decode(img_base64)))
    img.save(output_path)

    print(f"✅ AI-enhanced image saved as {output_path}")
    return output_path


def create_ai_enhanced_visual(image_prompt, narration=None, save_dir="generated_images"):
    """
    Searches Google for a reference image, enhances it with Gemini,
    and returns the final saved image path.
    """
    os.makedirs(save_dir, exist_ok=True)

    # 1️⃣ Find base image from Google
    base_images = google_image_search(image_prompt, num_images=1)
    reference_image_url = base_images[0] if base_images else None

    # 2️⃣ Generate enhanced image with narration included
    output_path = os.path.join(save_dir, "enhanced_image.png")
    final_path = generate_ai_enhanced_image(
        prompt=image_prompt,
        narration=narration,
        reference_image_url=reference_image_url,
        output_path=output_path
    )

    return final_path


# ✅ Example usage
if __name__ == "__main__":
    narration_points = [
        "Ions are atoms or molecules with an electric charge.",
        "Atoms become ions by gaining or losing electrons.",
        "Positive ions have lost electrons, while negative ions have gained electrons.",
        "Ions play crucial roles in chemical reactions and biological processes."
    ]

    narration_text = "\n".join([f"{i+1}. {point}" for i, point in enumerate(narration_points)])
    prompt = "illustration showing atoms gaining or losing electrons to become ions"
    final_image = create_ai_enhanced_visual(image_prompt=prompt, narration=narration_text)
    print(f"\nFinal Image Path: {final_image}")
