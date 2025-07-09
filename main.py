from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import random
import os
from typing import List

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "<OPENROUTER_API_KEY>")
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "<YOUR_SITE_URL>")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME", "<YOUR_SITE_NAME>")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_products_from_text(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines
import base64
# ...existing code...

@app.post("/extract-shopping-list")
async def extract_shopping_list(image: UploadFile = File(...)):
    # Read image bytes
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{image.content_type};base64,{image_base64}"

    # Call OpenRouter API
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # "HTTP-Referer": YOUR_SITE_URL,
            # "X-Title": YOUR_SITE_NAME,
        },
        data=json.dumps({
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the shopping list from this image. Only output the list, one item per line."},
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]
                }
            ],
        })
    )

    if response.status_code != 200:
        return {"error": "Failed to process image", "details": response.text}

    result = response.json()
    try:
        text = result["choices"][0]["message"]["content"]
    except Exception:
        return {"error": "Failed to parse OpenRouter response", "details": result}

    products = extract_products_from_text(text)
    if not products:
        return {"products": [], "not_available": None}

    not_available = random.choice(products)
    return {
        "products": products,
        "not_available": not_available
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)