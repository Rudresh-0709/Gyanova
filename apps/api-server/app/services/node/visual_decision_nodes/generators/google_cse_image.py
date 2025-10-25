import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
cse_id = os.getenv("GOOGLE_CSE_ID")

def google_image_search(query, num_images=1):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query, 
        "cx": cse_id,
        "key": api_key,
        "searchType": "image",
        "num": num_images  # you can request up to 10 images at once
    }
    response = requests.get(url, params=params)
    results = response.json()
    
    if "items" not in results:
        return []
    
    # return only top `num_images` links
    return [item["link"] for item in results["items"][:num_images]]

images = google_image_search("illustration showing different atoms with nucleus and orbiting electrons", num_images=1)
print(images)
