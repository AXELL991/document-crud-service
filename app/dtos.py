"""DTOs (Data Transfer Objects) del document-crud-service."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Payload para crear un documento."""

    filename: str = Field(..., description="Nombre del archivo PDF original")
    text: str = Field(..., description="Texto extraído del PDF")
    pages: int = Field(..., ge=1, description="Número de páginas del PDF")
    pdf_hash: str = Field(..., description="SHA-256 del PDF original")


class DocumentPatch(BaseModel):
    """Payload para actualizar parcialmente un documento."""

    filename: Optional[str] = None
    text: Optional[str] = None


class DocumentResponse(BaseModel):
    """Representación de un documento en las respuestas."""

    id: str
    filename: str
    text: str
    pages: int
    pdf_hash: str
    idempotency_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginatedDocuments(BaseModel):
    """Respuesta paginada de documentos."""

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
