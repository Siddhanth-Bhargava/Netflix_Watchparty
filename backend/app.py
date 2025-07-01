from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uuid

app = FastAPI()
rooms = {}

@app.get("/")
async def root():
    return {"message": "Watch party server running"}

@app.post("/create_room")
async def create_room():
    room_id = str(uuid.uuid4())[:8]
    rooms[room_id] = {"users": set(), "votes": {}, "state": {"playing": False, "time": 0}}
    return {"room_id": room_id}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    room = rooms.get(room_id)
    if room is None:
        await websocket.close()
        return
    room["users"].add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            for user in room["users"]:
                if user != websocket:
                    await user.send_json(data)
            if data["type"] in ["play", "pause"]:
                room["state"].update({"playing": data["type"]=="play", "time": data["time"]})
    except WebSocketDisconnect:
        room["users"].remove(websocket)
