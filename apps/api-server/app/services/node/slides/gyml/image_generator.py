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
    STYLE_UUIDS = {
        "3d render": "debdf72a-91a4-467b-bf61-cc02bdeb69c6",
        "acrylic": "3cbb655a-7ca4-463f-b697-8a03ad67327c",
        "anime general": "b2a54a51-230b-4d4f-ad4e-8409bf58645f",
        "creative": "6fedbf1f-4a17-45ec-84fb-92fe524a29ef",
        "dynamic": "111dc692-d470-4eec-b791-3475abac4c46",
        "fashion": "594c4a08-a522-4e0e-b7ff-e4dac4b6b622",
        "game concept": "09d2b5b5-d7c5-4c02-905d-9f84051640f4",
        "graphic design 3d": "7d7c2bc5-4b12-4ac3-81a9-630057e9e89f",
        "illustration": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70",
        "none": "556c1ee5-ec38-42e8-955a-1e82dad0ffa1",
        "portrait": "8e2bc543-6ee2-45f9-bcd9-594b6ce84dcd",
        "portrait cinematic": "4edb03c9-8a26-4041-9d01-f85b5d4abd71",
        "ray traced": "b504f83c-3326-4947-82e1-7fe9e839ec0f",
        "stock photo": "5bdc3f2a-1be6-4d1c-8e77-992a30824a2c",
        "watercolor": "1db308ce-c7ad-4d10-96fd-592fa6b75cc4",
    }

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

        async with httpx.AsyncClient(timeout=120.0) as client:
            generation_id = await cls._trigger_generation(
                client, prompt, width, height, style=style
            )
            if not generation_id:
                return None
            return await cls._poll_for_result(client, generation_id)

    @classmethod
    async def generate_accent_image(
        cls, prompt: str, layout: str, topic: str, style: Optional[str] = None
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
        width, height = (1024, 1024)  # FLUX requires 1024x1024

        # 2. Refine the prompt based on topic and layout
        refined_prompt = cls._enhance_prompt(
            prompt, topic, layout, style=style or "dynamic"
        )

        # 3. Request generation (Asynchronous)
        async with httpx.AsyncClient(timeout=120.0) as client:
            generation_id = await cls._trigger_generation(
                client, refined_prompt, width, height, style=style or "dynamic"
            )
            if not generation_id:
                return None

            # 4. Poll for the result
            image_url = await cls._poll_for_result(
                client, generation_id, max_attempts=40
            )
            return image_url

    @classmethod
    def _get_dimensions_for_layout(cls, layout: str) -> Tuple[int, int]:
        return (1024, 1024)  # FLUX strictly requires 1024x1024, CSS will crop it

    @staticmethod
    def _enhance_prompt(
        prompt: str, topic: str, layout: str, style: str = "dynamic"
    ) -> str:
        clean_prompt = str(prompt).strip().rstrip(".")

        if style == "simple_drawing":
            # Direct user request for "simple drawings or arts, nothing complex or involving words"
            style_suffix = "simple flat illustration, clean vector art, minimalist drawing, solid colors, no text, white background, professional educational graphic"
        elif style and style != "dynamic":
            # Custom style provided by user - strengthened for non-photographic results if style implies it
            extra = ""
            if (
                "illustration" in style.lower()
                or "art" in style.lower()
                or "drawing" in style.lower()
            ):
                extra = ", non-photographic, hand-drawn, artistic drawing, no realistic details, clean lines, flat 2d art style, stylized drawing, 2d vector look, absolute zero realism"
            style_suffix = (
                f"{style}{extra}, professional educational visual, high quality"
            )
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

        # Map the requested style to the corresponding Leonardo UUID
        style_lower = style.lower() if style else "dynamic"
        style_uuid = cls.STYLE_UUIDS.get(style_lower)  # Try exact match

        # If no exact match, try partial match (e.g., "illustration image" -> "illustration")
        if not style_uuid:
            for key, uuid in cls.STYLE_UUIDS.items():
                if key in style_lower:
                    style_uuid = uuid
                    break

        # Fallback to dynamic if still not found and not explicitly "none" or empty string
        if not style_uuid and style_lower != "none":
            style_uuid = cls.STYLE_UUIDS.get("dynamic")

        payload = {
            "modelId": cls.MODEL_ID,
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": 1,
            "enhancePrompt": False,
        }
        if style_uuid:
            payload["styleUUID"] = style_uuid

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
        cls, client: httpx.AsyncClient, generation_id: str, max_attempts: int = 40
    ) -> Optional[str]:
        """Poll the GET /generations/{id} endpoint until complete."""
        url = f"{cls.BASE_URL}/generations/{generation_id}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {LEONARDO_API_KEY}",
        }

        await asyncio.sleep(5)  # Initial wait for GPU to start

        for attempt in range(max_attempts):
            try:
                # Use a fresh client or specify a long timeout for each poll request to avoid individual poll timeouts
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
                    if images:
                        print(
                            f"   ✅ Leonardo Image Ready: {images[0].get('url')[:60]}..."
                        )
                        return images[0].get("url")
                    return None
                if status == "FAILED":
                    print(f"   ❌ Leonardo Generation FAILED for job {generation_id}")
                    return None

                # Still processing
                if attempt % 5 == 0:
                    print(f"   ⏳ Polling Leonardo ({attempt}/{max_attempts})...")

                await asyncio.sleep(2.5)
            except Exception as e:
                print(f"ERROR: Local error during polling: {e}")
                await asyncio.sleep(3)

        print(f"   ⚠ Polling timed out after {max_attempts} attempts.")
        return None
