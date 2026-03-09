import os
import asyncio
import httpx
from dotenv import load_dotenv

# Walk up to find .env
env_path = None
curr_dir = os.path.dirname(os.path.abspath(__file__))
for _ in range(6):
    pot = os.path.join(curr_dir, ".env")
    if os.path.exists(pot):
        env_path = pot
        break
    curr_dir = os.path.dirname(curr_dir)

if env_path:
    load_dotenv(env_path)

api_key = os.getenv("LEONARDO_API_KEY")


async def test_leonardo():
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }

    payload = {
        "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
        "prompt": "orange cat",
        "width": 1024,
        "height": 1024,
        "num_images": 1,
        "contrast": 3.5,
        "styleUUID": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        print("STATUS:", r.status_code)
        with open("err.txt", "w") as f:
            f.write(r.text)
        print("Wrote to err.txt")


if __name__ == "__main__":
    asyncio.run(test_leonardo())
