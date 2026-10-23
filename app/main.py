"""
Punto de entrada del document-crud-service.

Rutas:
  POST   /v1/documents              - Crear documento (con Idempotency-Key)
  GET    /v1/documents              - Listar documentos (paginado)
  GET    /v1/documents/{id}         - Obtener documento
  PATCH  /v1/documents/{id}         - Actualizar parcialmente
  DELETE /v1/documents/{id}         - Eliminar
  GET    /health/live               - Liveness probe
  GET    /health/ready              - Readiness probe (hace ping a Mongo)
"""
from __future__ import annotations

import logging
import secrets
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from app import repository
from app.api import routes
from app.core.config import settings
from app.core.exception_handlers import unhandled_exception_handler
from app.core.logging_config import configure_logging

configure_logging(settings.loglevel.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Conecta a MongoDB al arrancar y cierra la conexión al terminar."""
    await repository.connect()
    logger.info("document-crud-service iniciado")
    try:
        yield
    finally:
        await repository.disconnect()
        logger.info("document-crud-service detenido")


app = FastAPI(
    title="document-crud-service",
    description="CRUD de documentos PDF extraídos. Único dueño de MongoDB.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(Exception, unhandled_exception_handler)


# ---------------------------------------------------------------------------
# Middleware: X-Request-ID
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Auth interna (excluyendo /health/*)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def internal_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/health"):
        return await call_next(request)
    token = request.headers.get("X-Internal-Token", "")
    if not secrets.compare_digest(token.encode(), settings.internal_api_token.encode()):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Token interno inválido"})
    return await call_next(request)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------
@app.get("/health/live", tags=["health"])
async def health_live():
    """Liveness: el proceso está vivo."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    """Readiness: hace ping a MongoDB."""
    ok = await repository.ping()
    if not ok:
        raise HTTPException(status_code=503, detail="MongoDB no disponible")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Rutas CRUD
# ---------------------------------------------------------------------------
app.include_router(routes.router)
