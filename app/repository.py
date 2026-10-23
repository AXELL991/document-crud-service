"""
Capa de acceso a datos para document-crud-service.

Usa ``pymongo.AsyncMongoClient`` sobre MongoDB (no se usa motor).
Este servicio es el ÚNICO dueño de la base de datos 'document_crud_db'.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, AsyncMongoClient, IndexModel
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.dtos import DocumentCreate, DocumentPatch, DocumentResponse, PaginatedDocuments
from app.exceptions import DocumentNotFoundError, IdempotencyConflictError, TextTooLargeError

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None
_db = None


def get_db():
    if _db is None:
        raise RuntimeError("Base de datos no inicializada")
    return _db


async def connect() -> None:
    """Conecta a MongoDB con reintentos exponenciales y backoff."""
    global _client, _db

    for attempt in range(1, 6):
        try:
            _client = AsyncMongoClient(
                settings.mongo_uri,
                serverSelectionTimeoutMS=settings.mongo_timeout_ms,
            )
            await _client.admin.command("ping")
            _db = _client[settings.mongo_db_name]
            await _create_indexes()
            logger.info(
                "Conectado a MongoDB: %s / %s", settings.mongo_uri, settings.mongo_db_name
            )
            return
        except Exception as exc:
            wait = 2**attempt
            logger.warning(
                "Intento %d fallido al conectar a MongoDB: %s. Reintentando en %ds...",
                attempt,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

    raise RuntimeError("No se pudo conectar a MongoDB después de 5 intentos")


async def disconnect() -> None:
    """Cierra la conexión a MongoDB."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Conexión a MongoDB cerrada")


async def _create_indexes() -> None:
    """Crea los índices necesarios al arrancar."""
    db = get_db()
    await db.documents.create_indexes(
        [
            IndexModel([("idempotency_key", ASCENDING)], unique=True, name="idx_idempotency_key"),
            IndexModel([("created_at", ASCENDING)], name="idx_created_at"),
        ]
    )
    logger.info("Índices de MongoDB creados/verificados")


async def ping() -> bool:
    """Verifica que MongoDB responde."""
    try:
        if _client is None:
            return False
        await _client.admin.command("ping")
        return True
    except Exception:
        return False


def _to_response(doc: dict) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc["_id"]),
        filename=doc["filename"],
        text=doc["text"],
        pages=doc["pages"],
        pdf_hash=doc["pdf_hash"],
        idempotency_key=doc["idempotency_key"],
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at"),
    )


async def create_document(
    idempotency_key: str,
    payload: DocumentCreate,
) -> DocumentResponse:
    """
    Crea un documento. Implementa idempotencia:
    - Misma clave y mismo pdf_hash → devuelve el existente.
    - Misma clave y distinto pdf_hash → 409.
    """
    if len(payload.text.encode()) > settings.max_text_bytes:
        raise TextTooLargeError("El texto supera el límite permitido")

    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        "filename": payload.filename,
        "text": payload.text,
        "pages": payload.pages,
        "pdf_hash": payload.pdf_hash,
        "idempotency_key": idempotency_key,
        "created_at": now,
    }

    try:
        result = await db.documents.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_response(doc)
    except DuplicateKeyError:
        # Ya existe un doc con esa clave de idempotencia
        existing = await db.documents.find_one({"idempotency_key": idempotency_key})
        if existing and existing.get("pdf_hash") == payload.pdf_hash:
            return _to_response(existing)
        raise IdempotencyConflictError(
            f"La clave de idempotencia '{idempotency_key}' ya existe con un payload distinto"
        )


async def get_document(doc_id: str) -> DocumentResponse:
    db = get_db()
    try:
        oid = ObjectId(doc_id)
    except Exception:
        raise DocumentNotFoundError(f"ID inválido: {doc_id}")
    doc = await db.documents.find_one({"_id": oid})
    if not doc:
        raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")
    return _to_response(doc)


async def list_documents(page: int, page_size: int) -> PaginatedDocuments:
    db = get_db()
    page_size = min(page_size, settings.page_size_max)
    skip = (page - 1) * page_size
    total = await db.documents.count_documents({})
    cursor = db.documents.find({}).sort("created_at", ASCENDING).skip(skip).limit(page_size)
    items = [_to_response(doc) async for doc in cursor]
    return PaginatedDocuments(items=items, total=total, page=page, page_size=page_size)


async def patch_document(doc_id: str, patch: DocumentPatch) -> DocumentResponse:
    db = get_db()
    try:
        oid = ObjectId(doc_id)
    except Exception:
        raise DocumentNotFoundError(f"ID inválido: {doc_id}")
    update = {k: v for k, v in patch.model_dump().items() if v is not None}
    if not update:
        return await get_document(doc_id)
    update["updated_at"] = datetime.now(timezone.utc)
    result = await db.documents.find_one_and_update(
        {"_id": oid},
        {"$set": update},
        return_document=True,
    )
    if not result:
        raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")
    return _to_response(result)


async def delete_document(doc_id: str) -> None:
    db = get_db()
    try:
        oid = ObjectId(doc_id)
    except Exception:
        raise DocumentNotFoundError(f"ID inválido: {doc_id}")
    result = await db.documents.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")
