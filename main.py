from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import asyncio

from jobs.image_clean_up import delete_old_images
from jobs.image_fetcher import handle_image

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
            
clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            # Keep the WebSocket connection alive
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        clients.remove(websocket)
    finally:
        clients.remove(websocket)

@app.on_event("startup")
async def startup_event():
    app.state.background_task = asyncio.create_task(handle_image(clients))
    app.state.cleanup_task = asyncio.create_task(delete_old_images())

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
