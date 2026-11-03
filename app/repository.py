"""
Capa de acceso a datos para document-crud-service.

Usa ``pymongo.AsyncMongoClient`` sobre MongoDB. Este servicio es el ÚNICO
dueño de la base de datos. Todas las operaciones devuelven o aceptan entidades
de dominio (``Documento``) en lugar de dicts crudos de Mongo.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo import ASCENDING, AsyncMongoClient, IndexModel
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.dtos import DocumentPatch, PaginatedDocuments, DocumentResponse
from app.exceptions import DocumentNotFoundError, IdempotencyConflictError
from app.models.document import Documento

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None
_db = None


def get_db():
    if _db is None:
        raise RuntimeError("Base de datos no inicializada")
    return _db


class DocumentRepository:
    """Repositorio de documentos. Único punto de acceso a MongoDB."""

    def __init__(self):
        self._client: AsyncMongoClient | None = None
        self._db = None

    async def connect(self) -> None:
        """Conecta a MongoDB con reintentos exponenciales y backoff."""
        self._client = AsyncMongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=settings.mongo_timeout_ms,
        )
        await self._client.admin.command("ping")
        self._db = self._client[settings.mongo_db_name]
        await self._create_indexes()
        logger.info(
            "Conectado a MongoDB: %s / %s", settings.mongo_uri, settings.mongo_db_name
        )

    async def disconnect(self) -> None:
        """Cierra la conexión a MongoDB."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Conexión a MongoDB cerrada")

    async def ping(self) -> bool:
        """Verifica que MongoDB responde."""
        try:
            if self._client is None:
                return False
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    async def _create_indexes(self) -> None:
        """Crea los índices necesarios al arrancar."""
        db = self._db
        await db.documents.create_indexes(
            [
                IndexModel(
                    [("idempotency_key", ASCENDING)],
                    unique=True,
                    name="idx_idempotency_key",
                ),
                IndexModel([("created_at", ASCENDING)], name="idx_created_at"),
                IndexModel([("pdf_hash", ASCENDING)], name="idx_pdf_hash"),
            ]
        )
        logger.info("Índices de MongoDB creados/verificados")

    def _to_domain(self, doc: dict) -> Documento:
        """Convierte un dict de Mongo en una entidad de dominio."""
        return Documento.from_dict(doc)

    async def create(
        self, idempotency_key: str, documento: Documento
    ) -> Documento:
        """
        Crea un documento con control de idempotencia.

        - Misma clave y mismo pdf_hash → devuelve el existente.
        - Misma clave y distinto pdf_hash → 409.
        """
        db = self._db
        now = datetime.now(timezone.utc)
        doc = {
            "filename": documento.filename,
            "text": documento.text,
            "pages": documento.pages,
            "pdf_hash": documento.pdf_hash,
            "idempotency_key": idempotency_key,
            "owner_id": documento.owner_id,
            "created_at": now,
        }

        try:
            result = await db.documents.insert_one(doc)
            doc["_id"] = result.inserted_id
            return self._to_domain(doc)
        except DuplicateKeyError:
            existing = await db.documents.find_one(
                {"idempotency_key": idempotency_key}
            )
            if existing and existing.get("pdf_hash") == doc["pdf_hash"]:
                return self._to_domain(existing)
            raise IdempotencyConflictError(
                f"La clave de idempotencia '{idempotency_key}' ya existe con un payload distinto"
            )

    async def get_by_id(self, doc_id: str, owner_id: str) -> Documento:
        """Obtiene un documento por su ID de Mongo."""
        db = self._db
        try:
            oid = ObjectId(doc_id)
        except Exception:
            raise DocumentNotFoundError(f"ID inválido: {doc_id}")
        doc = await db.documents.find_one({"_id": oid, "owner_id": owner_id})
        if not doc:
            raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")
        return self._to_domain(doc)

    async def get_by_checksum(self, checksum: str, owner_id: str) -> Documento:
        """Obtiene un documento por su hash SHA-256."""
        db = self._db
        doc = await db.documents.find_one({"pdf_hash": checksum, "owner_id": owner_id})
        if not doc:
            raise DocumentNotFoundError(
                f"Documento con checksum {checksum} no encontrado"
            )
        return self._to_domain(doc)

    async def list(self, page: int, page_size: int) -> PaginatedDocuments:
        """Lista documentos de forma paginada."""
        db = self._db
        page_size = min(page_size, settings.page_size_max)
        skip = (page - 1) * page_size
        total = await db.documents.count_documents({})
        cursor = (
            db.documents.find({})
            .sort("created_at", ASCENDING)
            .skip(skip)
            .limit(page_size)
        )
        docs = [self._to_domain(doc) async for doc in cursor]
        return PaginatedDocuments(
            items=[
                DocumentResponse(
                    id=d.id,
                    filename=d.filename,
                    text=d.text,
                    pages=d.pages,
                    pdf_hash=d.pdf_hash,
                    idempotency_key=d.idempotency_key,
                    owner_id=d.owner_id,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
                for d in docs
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(
        self, doc_id: str, owner_id: str, patch: DocumentPatch
    ) -> Documento:
        """Actualiza parcialmente un documento."""
        db = self._db
        try:
            oid = ObjectId(doc_id)
        except Exception:
            raise DocumentNotFoundError(f"ID inválido: {doc_id}")
        update = {k: v for k, v in patch.model_dump().items() if v is not None}
        if not update:
            return await self.get_by_id(doc_id, owner_id)
        update["updated_at"] = datetime.now(timezone.utc)
        result = await db.documents.find_one_and_update(
            {"_id": oid, "owner_id": owner_id},
            {"$set": update},
            return_document=True,
        )
        if not result:
            raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")
        return self._to_domain(result)

    async def delete(self, doc_id: str, owner_id: str) -> None:
        """Elimina un documento por su ID."""
        db = self._db
        try:
            oid = ObjectId(doc_id)
        except Exception:
            raise DocumentNotFoundError(f"ID inválido: {doc_id}")
        result = await db.documents.delete_one({"_id": oid, "owner_id": owner_id})
        if result.deleted_count == 0:
            raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")