import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv("../../../.env")
api_key = os.getenv("LEONARDO_API_KEY")


async def test_leonardo():
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }

    # Test C: Strong prompt + dynamic UUID
    payload_c = {
        "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
        "contrast": 3.5,
        "prompt": "An illustration of an orange cat playing with a tennis ball with the text FLUX. vector art, flat 2d, minimalist drawing, highly stylized, non-photographic.",
        "num_images": 1,
        "width": 1024,
        "height": 1024,
        "styleUUID": "111dc692-d470-4eec-b791-3475abac4c46",  # User's dynamic
        "enhancePrompt": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Starting Test C (Prompt + Dynamic UUID)")
        r1 = await client.post(url, json=payload_c, headers=headers)
        print("C STATUS:", r1.status_code)
        if r1.status_code != 200:
            print(r1.text)
        else:
            gen_id = r1.json().get("sdGenerationJob", {}).get("generationId")
            await asyncio.sleep(15)
            r2 = await client.get(url + f"/{gen_id}", headers=headers)
            print(
                "C Image URL:",
                r2.json()
                .get("generations_by_pk", {})
                .get("generated_images", [{}])[0]
                .get("url"),
            )


if __name__ == "__main__":
    asyncio.run(test_leonardo())
