import os, httpx
from dotenv import load_dotenv

load_dotenv("../../../.env")
api_key = os.getenv("LEONARDO_API_KEY")
url = "https://cloud.leonardo.ai/api/rest/v1/generations"
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {api_key}",
}

payload = {
    "modelId": "1dd50843-d653-4516-a8e3-f0238ee453ff",
    "contrast": 3.5,
    "prompt": "a photo of an orange cat playing with a tennis ball with the text FLUX",
    "num_images": 4,
    "width": 1024,
    "height": 1024,
    "styleUUID": "111dc692-d470-4eec-b791-3475abac4c46",
    "enhancePrompt": False,
}
with httpx.Client() as c:
    r = c.post(url, json=payload, headers=headers)
    print("STATUS", r.status_code)
    print("RESPONSE", r.text)
