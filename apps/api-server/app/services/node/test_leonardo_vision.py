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

    payload4 = {
        "modelId": "5c232a9e-9061-4777-980a-ddc8e65647c6",  # Leonardo Vision XL
        "prompt": "A dramatic scene of a crowded 18th-century Paris street with passionate crowds, flags waving.",
        "width": 1024,
        "height": 768,
        "num_images": 1,
        "styleUUID": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70",  # Illustration
        "alchemy": True,  # Usually required for SDXL styles
        "enhancePrompt": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Starting Test 4 (Vision XL + UUID + Alchemy)")
        r4 = await client.post(url, json=payload4, headers=headers)
        print("T4 STATUS:", r4.status_code)
        if r4.status_code == 200:
            gen_id4 = r4.json().get("sdGenerationJob", {}).get("generationId")
            print("T4 Generation ID:", gen_id4)
        else:
            print(r4.text)


if __name__ == "__main__":
    asyncio.run(test_leonardo())
