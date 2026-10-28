"""
Rutas REST del document-crud-service.

Prefijo: /v1
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Query, status

from app import repository
from app.dtos import DocumentCreate, DocumentPatch, DocumentResponse, PaginatedDocuments
from app.exceptions import DocumentNotFoundError, IdempotencyConflictError, TextTooLargeError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["documentos"])


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Crea un documento. Implementa idempotencia mediante la cabecera Idempotency-Key."""
    try:
        return await repository.create_document(idempotency_key, owner_id, payload)
    except TextTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/documents", response_model=PaginatedDocuments)
async def list_documents(
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Documentos por página"),
):
    """Lista todos los documentos de forma paginada."""
    return await repository.list_documents(page=page, page_size=page_size)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Obtiene un documento por su ID. Solo el propietario puede acceder."""
    try:
        return await repository.get_document(doc_id, owner_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/documents/{doc_id}", response_model=DocumentResponse)
async def patch_document(
    doc_id: str,
    patch: DocumentPatch,
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Actualiza parcialmente un documento. Solo el propietario puede modificar."""
    try:
        return await repository.patch_document(doc_id, owner_id, patch)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Elimina un documento. Solo el propietario puede eliminar."""
    try:
        await repository.delete_document(doc_id, owner_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
