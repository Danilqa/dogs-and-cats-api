from fastapi import HTTPException
import httpx
from PIL import Image
import io
import base64
import asyncio
import os
import uuid

from consts import IMAGE_DIRECTORY
from jobs.image_recognizer import recognize

os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

async def fetch_image_as_base64(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")
        return response.text

def convert_base64_to_image(b64_string):
    if ',' in b64_string:
        b64_data = b64_string.split(',')[1]
    else:
        b64_data = b64_string 

    image_data = base64.b64decode(b64_data)
    image = Image.open(io.BytesIO(image_data))

    return image

async def handle_image(clients):
    while True: 
        try:
            if len(clients) == 0:
                await asyncio.sleep(10)
                continue

            base64_url = "https://replica-podcast.ru/some-image.txt"
            base64_data = await fetch_image_as_base64(base64_url)
            image = convert_base64_to_image(base64_data)
            file_name = f"{uuid.uuid4()}.jpg"
            file_path = os.path.join(IMAGE_DIRECTORY, file_name)
            image.save(file_path, format='JPEG')

            image_url = f"http://127.0.0.1:8000/static/images/{file_name}"
            disconnected_clients = set()
            for client in list(clients):
                try:
                    type = recognize(f"./static/images/{file_name}")
                    await client.send_json({"image_url": image_url, "type": type})
                except Exception as e:
                    print(f"Error sending message: {e}")
                    disconnected_clients.add(client)

            for client in disconnected_clients:
                clients.remove(client)

            await asyncio.sleep(10)     
        except Exception as e:
            print(f"Error in handle_image: {e}")  # Print any errors for debugging
            await asyncio.sleep(10)