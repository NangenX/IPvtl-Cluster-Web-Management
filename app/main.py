import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from app.api import servers as servers_api
from app.config import settings
from app.exceptions import IPvtlException, ServerNotFoundException, ChannelOperationException
from app.logging_config import setup_logging, get_logger
from app.models import Server
from app.services.poller import Poller

logger = get_logger(__name__)

app = FastAPI()

# Add global exception handlers
@app.exception_handler(ServerNotFoundException)
async def server_not_found_handler(request: Request, exc: ServerNotFoundException):
    logger.warning(f"Server not found: {exc.server_id}")
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message}
    )


@app.exception_handler(ChannelOperationException)
async def channel_operation_handler(request: Request, exc: ChannelOperationException):
    logger.error(f"Channel operation failed: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message}
    )


@app.exception_handler(IPvtlException)
async def ipvtl_exception_handler(request: Request, exc: IPvtlException):
    logger.error(f"IPvtl exception: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message}
    )


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
    setup_logging()
    logger.info("Starting application...")
    servers = load_servers_from_config()
    logger.info(f"Loaded {len(servers)} servers from configuration")
    app.state.poller = Poller(servers)
    await app.state.poller.start()
    logger.info("Poller started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    poller = getattr(app.state, "poller", None)
    if poller:
        await poller.stop()
        logger.info("Poller stopped successfully")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
