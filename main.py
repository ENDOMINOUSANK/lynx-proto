from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import random
import os
from typing import List
import base64
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv(override=True)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "<OPENROUTER_API_KEY>")
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "<YOUR_SITE_URL>")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME", "<YOUR_SITE_NAME>")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "<MISTRAL_API_KEY>")
# MISTRAL_MODEL = "pixtral-12b-latest" # 4.5
# MISTRAL_MODEL = "mistral-medium-latest" #4.3
MISTRAL_MODEL = "mistral-small-latest" #3.57
# MISTRAL_MODEL = "pixtral-large-latest"  # service tier cap limitations

# Pixtral 12B (pixtral-12b-latest)
# Pixtral Large 2411 (pixtral-large-latest)
# Mistral Medium 2505 (mistral-medium-latest)
# Mistral Small 2503 (mistral-small-latest)

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

@app.post("/extract-shopping-list")
async def extract_shopping_list(image: UploadFile = File(...)):
    # Read image bytes and encode as base64
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{image.content_type};base64,{image_base64}"

    # Prepare messages for Mistral API
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the shopping list from this image. Only output the list, one item per line. Instructure with quantity and unit if available. Do not include any other text or explanations."
                },
                {
                    "type": "image_url",
                    "image_url": image_data_url
                }
            ]
        }
    ]

    # Call Mistral API
    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        chat_response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages
        )
        text = chat_response.choices[0].message.content
    except Exception as e:
        return {"error": "Failed to process image with Mistral", "details": str(e)}

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







# import base64
# # ...existing code...

# @app.post("/extract-shopping-list")
# async def extract_shopping_list(image: UploadFile = File(...)):
#     # Read image bytes
#     image_bytes = await image.read()
#     image_base64 = base64.b64encode(image_bytes).decode("utf-8")
#     image_data_url = f"data:{image.content_type};base64,{image_base64}"

#     # Call OpenRouter API
#     response = requests.post(
#         url="https://openrouter.ai/api/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#             "Content-Type": "application/json",
#             "HTTP-Referer": YOUR_SITE_URL,
#             "X-Title": YOUR_SITE_NAME,
#         },
#         data=json.dumps({
#             "model": "qwen/qwen2.5-vl-72b-instruct:free",
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": "Extract the shopping list from this image. Only output the list, one item per line."},
#                         {"type": "image_url", "image_url": {"url": image_data_url}}
#                     ]
#                 }
#             ],
#         })
#     )

#     if response.status_code != 200:
#         return {"error": "Failed to process image", "details": response.text}

#     result = response.json()
#     try:
#         text = result["choices"][0]["message"]["content"]
#     except Exception:
#         return {"error": "Failed to parse OpenRouter response", "details": result}

#     products = extract_products_from_text(text)
#     if not products:
#         return {"products": [], "not_available": None}

#     not_available = random.choice(products)
#     return {
#         "products": products,
#         "not_available": not_available
#     }