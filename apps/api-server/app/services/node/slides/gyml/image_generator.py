import os
import asyncio
import httpx
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")


class ImageGenerator:
    """
    Handles image generation using Leonardo.AI FLUX Schnell model.
    Maps slide layouts to specific aspect ratios and enhances prompts.
    Uses async/await for non-blocking execution.
    """

    BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"
    MODEL_ID = "1dd50843-d653-4516-a8e3-f0238ee453ff"  # FLUX Schnell as requested

    # Style Presets (Dynamic is usually best for mixed educational content)
    DYNAMIC_STYLE_UUID = "111dc692-d470-4eec-b791-3475abac4c46"

    @classmethod
    async def generate_image(
        cls, prompt: str, width: int = 1024, height: int = 1024, style: str = "dynamic"
    ) -> Optional[str]:
        """Generic method to generate a single image."""
        if not LEONARDO_API_KEY:
            print(
                "WARNING: LEONARDO_API_KEY not found in environment. Skipping image generation."
            )
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            generation_id = await cls._trigger_generation(
                client, prompt, width, height, style=style
            )
            if not generation_id:
                return None
            return await cls._poll_for_result(client, generation_id)

    @classmethod
    async def generate_accent_image(
        cls, prompt: str, layout: str, topic: str
    ) -> Optional[str]:
        """
        Main entry point to generate an image.
        Returns the publicly accessible URL of the generated image.
        """
        if not LEONARDO_API_KEY:
            print(
                "WARNING: LEONARDO_API_KEY not found in environment. Skipping image generation."
            )
            return None

        # 1. Map layout to dimensions
        width, height = cls._get_dimensions_for_layout(layout)

        # 2. Refine the prompt based on topic and layout
        refined_prompt = cls._enhance_prompt(prompt, topic, layout)

        # 3. Request generation (Asynchronous)
        async with httpx.AsyncClient(timeout=30.0) as client:
            generation_id = await cls._trigger_generation(
                client, refined_prompt, width, height
            )
            if not generation_id:
                return None

            # 4. Poll for the result
            image_url = await cls._poll_for_result(client, generation_id)
            return image_url

    @staticmethod
    def _get_dimensions_for_layout(layout: str) -> Tuple[int, int]:
        """Returns (width, height) optimal for the given GyML layout."""
        layout = layout.lower()
        if layout in ["top", "bottom"]:
            return 1024, 320
        # Sidebar style (Left / Right) - 9:16 Portrait
        if layout in ["left", "right", "right-wide"]:
            return 576, 1024
        return 1024, 1024

    @staticmethod
    def _enhance_prompt(
        prompt: str, topic: str, layout: str, style: str = "dynamic"
    ) -> str:
        clean_prompt = str(prompt).strip().rstrip(".")

        if style == "simple_drawing":
            # Direct user request for "simple drawings or arts, nothing complex or involving words"
            style_suffix = "simple flat illustration, clean vector art, minimalist drawing, solid colors, no text, white background, professional educational graphic"
        else:
            style_suffix = "high-end photography, professional studio lighting, sharp focus, 8k resolution, cinematic composition"

        enhanced = f"{clean_prompt}. Subject: {topic}. Style: {style_suffix}"

        if layout in ["top", "bottom"]:
            enhanced += ", wide-angle panoramic view, horizontal composition"
        elif layout in ["left", "right"]:
            enhanced += ", vertical composition, centralized subject"
        return enhanced

    @classmethod
    async def _trigger_generation(
        cls,
        client: httpx.AsyncClient,
        prompt: str,
        width: int,
        height: int,
        style: str = "dynamic",
    ) -> Optional[str]:
        """Call the POST /generations endpoint."""
        url = f"{cls.BASE_URL}/generations"

        # Style UUIDs can be adjusted if we want specific Leonardo styles
        style_uuid = cls.DYNAMIC_STYLE_UUID

        payload = {
            "modelId": cls.MODEL_ID,
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": 1,
            "styleUUID": style_uuid,
            "contrast": 3.5,
            "enhancePrompt": False,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {LEONARDO_API_KEY}",
        }

        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("sdGenerationJob", {}).get("generationId")
        except Exception as e:
            print(f"ERROR: Leonardo Generation Request failed: {e}")
            return None

    @classmethod
    async def _poll_for_result(
        cls, client: httpx.AsyncClient, generation_id: str, max_attempts: int = 15
    ) -> Optional[str]:
        """Poll the GET /generations/{id} endpoint until complete."""
        url = f"{cls.BASE_URL}/generations/{generation_id}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {LEONARDO_API_KEY}",
        }

        await asyncio.sleep(4)  # Initial wait

        for attempt in range(max_attempts):
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                generation_data = data.get("generations_by_pk") or (
                    data.get("generations", [None])[0]
                )

                if not generation_data:
                    await asyncio.sleep(2)
                    continue

                status = generation_data.get("status")
                if status == "COMPLETE":
                    images = generation_data.get("generated_images", [])
                    return images[0].get("url") if images else None
                if status == "FAILED":
                    return None

                await asyncio.sleep(2)
            except Exception as e:
                print(f"ERROR: Local error during polling: {e}")
                await asyncio.sleep(2)

        return None
