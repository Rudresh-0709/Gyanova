import base64
from io import BytesIO

from langchain_google_genai import ChatGoogleGenerativeAI
from ....llm.model_loader import load_gemini_image
from PIL import Image
from langchain_core.messages import HumanMessage

import os

def generate_ai_enhanced_image(): 
    llm = load_gemini_image()
    response = llm.invoke(
        [
            {
                "role": "user",
                "content": "Create a clear, scientific illustration depicting a cell immersed in an isotonic solution. Show the semi-permeable membrane of the cell with an equal concentration of solute particles inside and outside. Use arrows to indicate that water molecules are moving freely and equally both into and out of the cell, resulting in no overall change in cell size or shape. Use a clean, diagrammatic style with clear visual balance.",
            }
        ],
        generation_config = {
            "response_modalities": ["TEXT", "IMAGE"]
        }
    )
    image_part = None
    for part in response.content:
        # Check if the part is a dictionary AND contains the 'image_url' key
        if isinstance(part, dict) and 'image_url' in part:
            image_part = part
            break

    if image_part:
        # Extract the base64 part
        img_base64 = image_part['image_url']['url'].split('base64,')[-1]
        
        # Decode and save the image
        img = Image.open(BytesIO(base64.b64decode(img_base64)))
        img.save("langchain_generated_image.png")
        print("✅ Image generated and saved as 'langchain_generated_image.png'")
    else:
        # This block handles the case where no image part was found
        print("❌ Image generation failed. Model response content was:")
        print(response.content) 
        print("\nTip: Check if the model returned a safety block message or a quota error.")