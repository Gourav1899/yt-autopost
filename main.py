"""
TubeAutomate v3 — FastAPI + Multi-Channel Bot
Same Render service pe chalega
"""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from http.server import HTTPServer, BaseHTTPRequestHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.channels import router as channels_router
from routes.queue import router as queue_router
from routes.analytics import router as analytics_router
from routes.admin import router as admin_router
from scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 TubeAutomate API Starting...")
    # Scheduler background thread mein chalao
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
    log.info("⏰ Multi-channel scheduler started!")
    yield
    log.info("👋 Shutting down...")


app = FastAPI(
    title="TubeAutomate API",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production mein Lovable URL daalo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels_router,  prefix="/channels",  tags=["Channels"])
app.include_router(queue_router,     prefix="/queue",     tags=["Queue"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin_router,     prefix="/admin",     tags=["Admin"])


@app.get("/")
async def root():
    return {"status": "running ✅", "app": "TubeAutomate", "version": "3.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
