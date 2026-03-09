import os
import httpx
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


base_payload = {
    "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
    "prompt": "orange cat",
    "num_images": 1,
    "width": 1024,
    "height": 1024,
}

test_payload("Base FLUX", base_payload)
test_payload("+contrast", {**base_payload, "contrast": 3.5})
test_payload(
    "+styleUUID (Dynamic)",
    {**base_payload, "styleUUID": "111dc692-d470-4eec-b791-3475abac4c46"},
)
test_payload(
    "+styleUUID (Illust)",
    {**base_payload, "styleUUID": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70"},
)
test_payload("+enhancePrompt", {**base_payload, "enhancePrompt": False})

base_vision = {
    "modelId": "5c232a9e-9061-4777-980a-ddc8e65647c6",
    "prompt": "orange cat",
    "num_images": 1,
    "width": 1024,
    "height": 1024,
}

test_payload("Base Vision XL", base_vision)
test_payload("Vision+alchemy", {**base_vision, "alchemy": True})
test_payload(
    "Vision+alchemy+style",
    {
        **base_vision,
        "alchemy": True,
        "styleUUID": "645e4195-f63d-4715-a3f2-3fb1e6eb8c70",
    },
)
