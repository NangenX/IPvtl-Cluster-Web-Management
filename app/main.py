import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import servers as servers_api
from app.config import settings
from app.models import Server
from app.services.poller import Poller

app = FastAPI()
app.include_router(servers_api.router)

templates = Jinja2Templates(directory="frontend")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_servers_from_config():
    try:
        with open(settings.SERVERS_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Server(**s) for s in data]
    except Exception:
        return []


@app.on_event("startup")
async def startup_event():
    servers = load_servers_from_config()
    app.state.poller = Poller(servers)
    await app.state.poller.start()


@app.on_event("shutdown")
async def shutdown_event():
    poller = getattr(app.state, "poller", None)
    if poller:
        await poller.stop()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
