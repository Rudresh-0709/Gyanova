import requests, base64, mimetypes

import requests, base64

def fetch_and_encode_image_for_llama(url: str):
    """
    Downloads an image from URL and returns a Groq-compatible image object
    using 'image_data': {'b64_json': ...}.
    Works for Llama 4 Maverick Vision model.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "image/*,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # Encode image to base64
        img_b64 = base64.b64encode(resp.content).decode("utf-8")

        # ✅ Return proper Groq-compatible vision object
        return {
            "type": "image",
            "image_data": {"b64_json": img_b64}
        }

    except Exception as e:
        print(f"⚠️ Failed to fetch or encode image for Llama Vision: {e}")
        return None



def download_and_encode_image(url: str):
    """
    Downloads an image from a URL and returns a base64 data URI.
    Automatically follows redirects and handles .jpg, .png, .webp, .svg gracefully.
    Returns None if the image cannot be downloaded or decoded.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "image/*,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()

        # Infer MIME type
        mime = resp.headers.get("Content-Type")
        if not mime:
            mime = mimetypes.guess_type(url)[0] or "image/png"

        # Handle unsupported formats gracefully
        if "svg" in mime.lower() or url.endswith(".svg"):
            print(f"⚠️ Skipping unsupported SVG image: {url}")
            return None

        img_base64 = base64.b64encode(resp.content).decode("utf-8")
        data_uri = f"data:{mime};base64,{img_base64}"
        return data_uri

    except Exception as e:
        print(f"⚠️ Failed to download or encode image from {url}: {e}")
        return None
