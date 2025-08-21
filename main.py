from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import base64
from mistralai import Mistral
from dotenv import load_dotenv
import re
import asyncio

load_dotenv(override=True)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "<MISTRAL_API_KEY>")
MISTRAL_MODEL = "mistral-small-latest"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global camera state
cam_on = False

@app.post("/extract-main-info")
async def extract_main_info(image: UploadFile = File(...)):
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{image.content_type};base64,{image_base64}"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "From this image, extract the main value or identifier. "
                        "It may be a weighing scale metric (number with units) or a product number (often with slashes, e.g., '123/456'). "
                        "Only output the main extracted value, nothing else."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": image_data_url
                }
            ]
        }
    ]

    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        chat_response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages
        )
        text = chat_response.choices[0].message.content.strip()
    except Exception as e:
        return {"error": "Failed to process image with Mistral", "details": str(e)}

    # Optionally, use regex to extract a value with slashes or a number with units
    match = re.search(r"\b\d+/\d+\b", text)  # e.g., 123/456
    if not match:
        match = re.search(r"\b\d+(\.\d+)?\s*\w+\b", text)  # e.g., 12.5 kg
    main_value = match.group(0) if match else text

    return {"main_value": main_value}

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.post("/set-cam-state")
async def set_cam_state(request: Request):
    global cam_on
    data = await request.json()
    cam_on = bool(data.get("on", False))
    return {"cam_on": cam_on}

@app.websocket("/ws/cam-state")
async def cam_state_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"cam_on": cam_on})
            await asyncio.sleep(1)  # Send state every second
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




