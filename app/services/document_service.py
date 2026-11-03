"""
Capa de servicio/negocio del document-crud-service.

Orquesta las reglas de negocio sobre documentos: validaciones, idempotencia,
y delega la persistencia al repositorio. No conoce detalles de HTTP ni de MongoDB.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.dtos import DocumentCreate, DocumentPatch, PaginatedDocuments
from app.exceptions import DocumentNotFoundError, IdempotencyConflictError, TextTooLargeError
from app.models.document import Documento
from app.repository import DocumentRepository


class DocumentService:
    """Servicio de dominio para operaciones sobre documentos."""

    def __init__(self, repository: DocumentRepository):
        self._repository = repository

    async def create_document(
        self,
        idempotency_key: str,
        owner_id: str,
        payload: DocumentCreate,
    ) -> Documento:
        """
        Crea un documento con control de idempotencia.

        Reglas:
        - El texto no debe exceder MAX_TEXT_BYTES.
        - Misma idempotency_key + mismo pdf_hash → devuelve el existente.
        - Misma idempotency_key + distinto pdf_hash → 409.
        """
        if len(payload.text.encode()) > settings.max_text_bytes:
            raise TextTooLargeError("El texto supera el límite permitido")

        documento = Documento(
            filename=payload.filename,
            text=payload.text,
            pages=payload.pages,
            pdf_hash=payload.pdf_hash,
            idempotency_key=idempotency_key,
            owner_id=owner_id,
            created_at=datetime.now(timezone.utc),
        )

        return await self._repository.create(idempotency_key, documento)

    async def get_document(self, doc_id: str, owner_id: str) -> Documento:
        """Obtiene un documento por su ID interno (Mongo ObjectId)."""
        return await self._repository.get_by_id(doc_id, owner_id)

    async def get_document_by_checksum(self, checksum: str, owner_id: str) -> Documento:
        """Obtiene un documento por su hash SHA-256 (checksum)."""
        return await self._repository.get_by_checksum(checksum, owner_id)

    async def list_documents(self, page: int, page_size: int) -> PaginatedDocuments:
        """Lista documentos de forma paginada."""
        return await self._repository.list(page, page_size)

    async def patch_document(
        self, doc_id: str, owner_id: str, patch: DocumentPatch
    ) -> Documento:
        """Actualiza parcialmente un documento."""
        return await self._repository.update(doc_id, owner_id, patch)

    async def delete_document(self, doc_id: str, owner_id: str) -> None:
        """Elimina un documento por su ID."""
        await self._repository.delete(doc_id, owner_id)