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


def test_vision(w, h, style_uuid=None, alchemy=None, photoreal=None):
    payload = {
        "modelId": "5c232a9e-9061-4777-980a-ddc8e65647c6",  # Vision XL
        "prompt": "A completely flat vector illustration. NO realism. Flat colors.",
        "num_images": 1,
        "width": w,
        "height": h,
    }
    if style_uuid:
        payload["styleUUID"] = style_uuid
    if alchemy is not None:
        payload["alchemy"] = alchemy
    if photoreal is not None:
        payload["photoReal"] = photoreal

    print(
        f"Testing Vision XL {w}x{h} UUID={style_uuid} alchemy={alchemy} photoreal={photoreal}"
    )
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            print(
                "SUCCESS! Generation ID:", r.json()["sdGenerationJob"]["generationId"]
            )
            return True
        else:
            print(f"FAILED (Status {r.status_code}): {r.text}")
            return False


# Vision XL optimal resolutions according to Leonardo documentation are usually 1024x1024 or 1536x1024
test_vision(1024, 1024, "645e4195-f63d-4715-a3f2-3fb1e6eb8c70", alchemy=True)
test_vision(1024, 1024, "645e4195-f63d-4715-a3f2-3fb1e6eb8c70", alchemy=False)
test_vision(1024, 1024)
