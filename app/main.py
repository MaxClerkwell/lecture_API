import asyncio
import random
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException

app = FastAPI()
# In-memory storage for objects
to_save = []

@app.post("/add_object")
async def add_object(item: dict):
    """
    Adds a JSON object to the in-memory 'to_save' list.
    Generates a UUID for the object if not provided.
    """
    # Assign a new UUID if not present
    if "uuid" not in item:
        item["uuid"] = str(uuid.uuid4())
    to_save.append(item)
    return {"message": "Object added", "uuid": item["uuid"]}

@app.get("/object_list")
async def get_objects():
    """
    Returns all objects stored in the list.
    """
    return {"objects": to_save}

@app.delete("/delete_object/{object_uuid}")
async def delete_object(object_uuid: str):
    """
    Deletes an object by its UUID.
    Returns 404 if the UUID is not found.
    """
    for index, obj in enumerate(to_save):
        if obj.get("uuid") == object_uuid:
            to_save.pop(index)
            return {"message": "Object deleted", "uuid": object_uuid}
    # If not found, raise 404
    raise HTTPException(status_code=404, detail="Object not found")

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    mean: float = Query(..., description="Mean for the normally distributed random values"),
    std: float = Query(..., description="Standard deviation"),
    interval: int = Query(..., description="Interval in milliseconds between values")
):
    """
    WebSocket endpoint that continuously sends normally distributed random values.

    Query Parameters:
    - mean: Mean of the distribution
    - std: Standard deviation of the distribution
    - interval: Interval in milliseconds between generated values
    """
    await websocket.accept()
    try:
        while True:
            # Generate a value from a normal distribution
            value = random.gauss(mean, std)
            # Sleep for the specified interval (convert ms to seconds)
            await asyncio.sleep(interval / 1000)
            # Send the generated value back as JSON
            await websocket.send_json({"value": value})
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_app:app", host="0.0.0.0", port=8000, reload=True
    )
