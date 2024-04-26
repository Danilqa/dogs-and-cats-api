from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
from PIL import Image
import io
import base64
import asyncio
import os
import uuid
import time

app = FastAPI()

# Directory to store and serve images
image_directory = "./static/images"
os.makedirs(image_directory, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

async def fetch_image_as_base64(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")
        return response.text

def convert_base64_to_image(b64_string):
    if ',' in b64_string:  # Check if the comma is in the string to split correctly
        b64_data = b64_string.split(',')[1]  # Split and take the second part
    else:
        b64_data = b64_string  # If no comma, assume the whole string is base64 data

    image_data = base64.b64decode(b64_data)
    image = Image.open(io.BytesIO(image_data))
    if image.mode == 'RGBA':
        image = image.convert('RGB')  # Convert RGBA to RGB if necessary
    return image

async def delete_old_images(directory, age_limit=60):  # age_limit in seconds (5 minutes)
    while True:
        try:
            now = time.time()
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.stat(file_path).st_mtime < now - age_limit:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")  # Optional: print or log the deletion
        except Exception as e:
            print(f"Error deleting files: {e}")  # Handle potential errors in file deletion
        await asyncio.sleep(60)  # Check every 60 seconds

async def handle_image(clients):
    while True:  # This ensures the loop runs indefinitely
        try:
            if len(clients) == 0:
                print("No clients, skip")
                await asyncio.sleep(10)
                continue

            base64_url = "https://replica-podcast.ru/some-image.txt"
            base64_data = await fetch_image_as_base64(base64_url)
            image = convert_base64_to_image(base64_data)
            file_name = f"{uuid.uuid4()}.jpg"
            file_path = os.path.join(image_directory, file_name)
            image.save(file_path, format='JPEG')

            # Send the URL to the WebSocket clients
            image_url = f"http://127.0.0.1:8000/static/images/{file_name}"
            disconnected_clients = set()
            for client in list(clients):
                try:
                    await client.send_json({"image_url": image_url})
                except Exception as e:
                    print(f"Error sending message: {e}")
                    disconnected_clients.add(client)

            for client in disconnected_clients:
                clients.remove(client)

            await asyncio.sleep(10)     
        except Exception as e:
            print(f"Error in handle_image: {e}")  # Print any errors for debugging
            await asyncio.sleep(10)
            

clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(10)  # Keep the WebSocket connection alive
    except WebSocketDisconnect:
        clients.remove(websocket)
    finally:
        clients.remove(websocket)  # Ensure removal on disconnect

@app.on_event("startup")
async def startup_event():
    app.state.background_task = asyncio.create_task(handle_image(clients))
    app.state.cleanup_task = asyncio.create_task(delete_old_images(image_directory))

@app.on_event("shutdown")
async def shutdown_event():
    tasks = [app.state.image_task, app.state.cleanup_task]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
