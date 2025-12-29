import asyncio
from contextlib import asynccontextmanager
import logging
import os  
import pathlib
from typing import List
from urllib.parse import urlparse, urlunparse


import dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import ngrok
import uvicorn

from config_utils import load_config
from controller import Controller
from notifier import SlackNotifier

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_DEFAULT_PORT = 12345
_ASSETS_FOLDER = pathlib.Path(__file__).parent / "assets"
if not _ASSETS_FOLDER.exists():
    raise RuntimeError(f"Assets directory not found at {_ASSETS_FOLDER}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await _use_ngrok_if_needed(app.state.cfg)
    
    app.state.notifier = SlackNotifier(app.state.cfg["notifier"])
    await app.state.notifier.init()
    app.state.controller = Controller(app.state.cfg["controller"], app.state.notifier)
    yield
    await app.state.ngrok_listener.close()
    await app.state.ngrok_session.close()


async def expose_server_with_ngrok(port):
    session = await ngrok.SessionBuilder().authtoken(os.getenv("NGROK_AUTH_TOKEN")).connect()
    listener = await session.http_endpoint().listen()
    print (f"Ngrok ingress established at {listener.url()}")
    listener.forward(f"localhost:{port}")
    return listener.url()


async def _use_ngrok_if_needed(cfg):
    if "use_ngrok" not in cfg["server"] or not cfg["server"]["use_ngrok"]:
        return

    logger.info("Exposing server with ngrok")
    external_server_url = await expose_server_with_ngrok(cfg["server"]["port"])

    parsed_url = urlparse(cfg["notifier"]["assets_url"])
    parsed_ngrok_url = urlparse(external_server_url)
        
    new_assets_url = urlunparse((
        parsed_ngrok_url.scheme,                 # Use ngrok scheme
        parsed_ngrok_url.netloc,                 # Use ngrok netloc
        parsed_url.path,                         # Keep original path
        None, None, None
    ))
    cfg["notifier"]["assets_url"] = new_assets_url


def build_app(cfg):
    app = FastAPI(lifespan=lifespan)
    app.state.cfg = cfg
    
    # WebSocket connections for microphone test streaming
    active_ws_connections: List[WebSocket] = []

    @app.get("/ping")
    async def ping():
        logger.info("Ping received")
        return JSONResponse(content={"status": "ok"})

    @app.post("/pingpong-event")
    async def pingpong_event(request: Request):
        try:
            data = await request.json()
        except Exception:
            logger.error("Invalid JSON: %s", await request.body())
            return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
        
        try:
            await app.state.controller.handle_event(data)
            return JSONResponse(content={"status": "ok"})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JSONResponse(status_code=500, content={"error": "Error handling event"})

    @app.get("/room-state")
    async def room_state():
        return JSONResponse(content=app.state.controller.get_room_state())

    @app.websocket("/ws/audio-stream")
    async def audio_stream_ws(websocket: WebSocket):
        """WebSocket endpoint for streaming audio data to web clients"""
        await websocket.accept()
        active_ws_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(active_ws_connections)}")
        try:
            # Keep connection alive and wait for messages (or disconnection)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            active_ws_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(active_ws_connections)}")
    
    @app.post("/audio-samples")
    async def receive_audio_samples(request: Request):
        """Receive audio samples from ESP32 device and broadcast to WebSocket clients"""
        try:
            data = await request.json()
        except Exception:
            logger.error("Invalid JSON in audio samples: %s", await request.body())
            return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
        
        if "samples" not in data:
            return JSONResponse(status_code=400, content={"error": "Missing 'samples' field"})
        
        # Broadcast to all connected WebSocket clients
        if active_ws_connections:
            disconnected = []
            for connection in active_ws_connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket client: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                if conn in active_ws_connections:
                    active_ws_connections.remove(conn)
        
        return JSONResponse(content={"status": "ok", "clients": len(active_ws_connections)})

    app.mount("/assets", StaticFiles(directory=_ASSETS_FOLDER), name="assets")

    return app


cfg = load_config("backend/config.json")
app = build_app(cfg)

if __name__ == "__main__":
    try: 
        reload = os.getenv("RELOAD", "").strip().lower() in ("1", "true", "yes")
        uvicorn.run(
            "server:app",
            host=cfg["server"]["ip"],
            port=cfg["server"]["port"],
            log_level="debug",
            reload=reload,
        )
    finally:
        try:
            ngrok.disconnect()
        except Exception:
            pass