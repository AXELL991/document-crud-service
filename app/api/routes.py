"""
Rutas REST del document-crud-service.

Capa de presentación: los handlers son finos. Validan la entrada HTTP y delegan
el trabajo al servicio de negocio (``DocumentService``), resuelto dinámicamente
desde ``app.main`` para permitir inyección de dobles en tests.
Prefijo: /v1
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.dtos import DocumentCreate, DocumentPatch
from app.exceptions import DocumentNotFoundError, IdempotencyConflictError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["documentos"])


def _get_document_service():
    from app.main import document_service
    return document_service


def _doc_to_json(doc) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "text": doc.text,
        "pages": doc.pages,
        "pdf_hash": doc.pdf_hash,
        "idempotency_key": doc.idempotency_key,
        "owner_id": doc.owner_id,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Crea un documento. Implementa idempotencia mediante la cabecera Idempotency-Key."""
    try:
        doc = await _get_document_service().create_document(
            idempotency_key=idempotency_key,
            owner_id=owner_id,
            payload=payload,
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return JSONResponse(status_code=201, content=_doc_to_json(doc))


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Documentos por página"),
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Lista documentos de forma paginada filtrados por propietario."""
    result = await _get_document_service().list_documents(page=page, page_size=page_size, owner_id=owner_id)
    return JSONResponse(
        content={
            "items": [_doc_to_json(d) for d in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
        }
    )


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, owner_id: str = Header(..., alias="X-Owner-Id")):
    """Obtiene un documento por su ID. Solo el propietario puede acceder."""
    try:
        doc = await _get_document_service().get_document(doc_id=doc_id, owner_id=owner_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return JSONResponse(content=_doc_to_json(doc))


@router.get("/documents/checksum/{checksum}")
async def get_document_by_checksum(
    checksum: str, owner_id: str = Header(..., alias="X-Owner-Id")
):
    """Obtiene un documento por su hash SHA-256 (checksum)."""
    try:
        doc = await _get_document_service().get_document_by_checksum(
            checksum=checksum, owner_id=owner_id
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return JSONResponse(content=_doc_to_json(doc))


@router.patch("/documents/{doc_id}")
async def patch_document(
    doc_id: str,
    patch: DocumentPatch,
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Actualiza parcialmente un documento. Solo el propietario puede modificar."""
    try:
        doc = await _get_document_service().patch_document(
            doc_id=doc_id, owner_id=owner_id, patch=patch
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return JSONResponse(content=_doc_to_json(doc))


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    owner_id: str = Header(..., alias="X-Owner-Id"),
):
    """Elimina un documento. Solo el propietario puede eliminar."""
    try:
        await _get_document_service().delete_document(doc_id=doc_id, owner_id=owner_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return JSONResponse(status_code=204, content=None)