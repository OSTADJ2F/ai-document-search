import logging
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.auth.routes import router as auth_router
from app.config import get_settings
from app.database import models  # noqa: F401
from app.database.session import Base, engine
from app.documents.routes import router as documents_router

settings = get_settings()
logging.basicConfig(level=settings.log_level)
structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env != "production":
        Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="AI Document Search API",
    version="0.1.0",
    description="Private document ingestion, hybrid retrieval, and grounded answers.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request.complete",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.perf_counter() - started) * 1000, 2),
    )
    return response


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
