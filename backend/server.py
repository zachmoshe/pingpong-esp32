import asyncio
from contextlib import asynccontextmanager
import logging
import os  
import pathlib
from urllib.parse import urlparse, urlunparse


import dotenv
from fastapi import FastAPI, Request
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


def build_app(cfg)  :
    app = FastAPI(lifespan=lifespan)
    app.state.cfg = cfg

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

    app.mount("/assets", StaticFiles(directory=_ASSETS_FOLDER), name="assets")

    return app

cfg = load_config("backend/config.json")
# _use_ngrok_if_needed(cfg)
app = build_app(cfg)

if __name__ == "__main__":
    try: 
        uvicorn.run("server:app", host=cfg["server"]["ip"], port=cfg["server"]["port"], log_level="debug", reload=True)
    finally:
        ngrok.disconnect()