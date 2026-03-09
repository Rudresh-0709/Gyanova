import os, httpx, asyncio
from dotenv import load_dotenv

load_dotenv("../../../.env")
api_key = os.getenv("LEONARDO_API_KEY")
url = "https://cloud.leonardo.ai/api/rest/v1/generations"
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {api_key}",
}


def test_payload(name, payload):
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload, headers=headers)
        print(f"{name} STATUS: {r.status_code}")
        if r.status_code != 200:
            print(f"ERROR: {r.text}")


# Test FLUX 1024x1024
test_payload(
    "FLUX 1024x1024",
    {
        "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
        "prompt": "test cat",
        "num_images": 1,
        "width": 1024,
        "height": 1024,
        "enhancePrompt": False,
    },
)

# Test FLUX 1024x768
test_payload(
    "FLUX 1024x768",
    {
        "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
        "prompt": "test cat",
        "num_images": 1,
        "width": 1024,
        "height": 768,
        "enhancePrompt": False,
    },
)

# Test FLUX 1024x1024 with StyleUUID Illustration
test_payload(
    "FLUX 1024x1024 + UUID",
    {
        "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
        "prompt": "test cat",
        "num_images": 1,
        "width": 1024,
        "height": 1024,
        "styleUUID": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70",
        "enhancePrompt": False,
    },
)

# Test Lightning XL 1024x768 with StyleUUID Illustration (alchemy needed?)
test_payload(
    "Lightning XL 1024x768 + UUID + Alchemy",
    {
        "modelId": "b24e16ff-06e3-43eb-8d33-4416c2d75876",
        "prompt": "test cat",
        "num_images": 1,
        "width": 1024,
        "height": 768,
        "styleUUID": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70",
        "alchemy": True,
        "enhancePrompt": False,
    },
)
