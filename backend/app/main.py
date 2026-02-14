"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth, subscriptions, papers, stars, system
from app.services.scheduler import start_scheduler, shutdown_scheduler, restore_scheduled_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    if settings.SCHEDULER_ENABLED:
        logger.info("Starting scheduler...")
        start_scheduler()
        await restore_scheduled_jobs()
    else:
        logger.info("Scheduler disabled by configuration.")
    logger.info("ArxivDigest backend ready.")
    yield
    # Shutdown
    if settings.SCHEDULER_ENABLED:
        shutdown_scheduler()
    logger.info("ArxivDigest backend shut down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS – allow the Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(subscriptions.router)
app.include_router(papers.router)
app.include_router(stars.router)
app.include_router(system.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "env": settings.ENV}
