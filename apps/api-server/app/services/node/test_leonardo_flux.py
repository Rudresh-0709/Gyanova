import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load key from parent dir
load_dotenv(".env")
api_key = os.getenv("LEONARDO_API_KEY")


async def test_leonardo():
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }

    # Test 3: Strong prefix ONLY (No styleUUID for FLUX)
    payload3 = {
        "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",  # FLUX Schnell
        "prompt": "Vector illustration, flat 2d art, minimalist drawing, highly stylized, non-photographic, zero realism. A dramatic scene of a crowded 18th-century Paris street with passionate crowds, flags waving.",
        "width": 1024,
        "height": 512,
        "num_images": 1,
        "enhancePrompt": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Starting Test 3 (Prompt ONLY)")
        r3 = await client.post(url, json=payload3, headers=headers)
        print("T3 STATUS:", r3.status_code)
        if r3.status_code == 200:
            gen_id3 = r3.json().get("sdGenerationJob", {}).get("generationId")
            print("T3 Generation ID:", gen_id3)
        else:
            print(r3.text)

        await asyncio.sleep(15)
        print("\nChecking results...")

        if r3.status_code == 200:
            status3 = await client.get(
                f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id3}",
                headers=headers,
            )
            print(
                "T3 Image Output:",
                status3.json()
                .get("generations_by_pk", {})
                .get("generated_images", [{}])[0]
                .get("url"),
            )


if __name__ == "__main__":
    asyncio.run(test_leonardo())
