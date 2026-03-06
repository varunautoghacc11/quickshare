import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.storage import init_redis, close_redis
from app.routers import share, receive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting QuickShare API...")
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory ready: {upload_dir}")
    await init_redis(settings.REDIS_URL)
    yield
    # Shutdown
    logger.info("Shutting down QuickShare API...")
    await close_redis()


app = FastAPI(
    title="QuickShare API",
    description="Temporary device-to-device file and text sharing with 6-digit codes.",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = list(settings.CORS_ORIGINS)
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(share.router, prefix="/api/share", tags=["share"])
app.include_router(receive.router, prefix="/api/receive", tags=["receive"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "quickshare-api"}
