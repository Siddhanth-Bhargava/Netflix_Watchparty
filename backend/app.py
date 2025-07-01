from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
rooms = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Watch party server running"}

@app.post("/create_room")
async def create_room():
    room_id = str(uuid.uuid4())[:8]
    rooms[room_id] = {"users": set(), "votes": {}, "state": {"playing": False, "time": 0}}
    print(f"[DEBUG] Room created: {room_id}")
    return {"room_id": room_id}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    room = rooms.get(room_id)
    if room is None:
        await websocket.close()
        return
    room["users"].add(websocket)
    print(f"[DEBUG] User {id(websocket)} connected to room {room_id}. Users: {[id(u) for u in room['users']]}")
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast all updates: play, pause, chat, vote
            for user in room["users"]:
                if user != websocket:
                    await user.send_json(data)
            if data["type"] in ["play", "pause"]:
                room["state"].update({"playing": data["type"]=="play", "time": data["time"]})
            if data["type"] == "vote":
                user_id = data.get("user_id", str(id(websocket)))
                vote = data.get("vote")
                room["votes"][user_id] = vote
            # Optionally handle chat, etc.
    except WebSocketDisconnect:
        room["users"].remove(websocket)
        print(f"[DEBUG] User {id(websocket)} disconnected from room {room_id}. Users: {[id(u) for u in room['users']]}")
        if not room["users"]:
            del rooms[room_id]
            print(f"[DEBUG] Room {room_id} deleted (empty)")
