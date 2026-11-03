"""Entidad de dominio Documento.

Representa un documento PDF procesado y persistido en MongoDB.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional


class Documento:
    """Entidad de dominio del documento."""

    def __init__(
        self,
        filename: str,
        text: str,
        pages: int,
        pdf_hash: str,
        idempotency_key: str,
        owner_id: str,
        created_at: datetime,
        id: Optional[str] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.filename = filename
        self.text = text
        self.pages = pages
        self.pdf_hash = pdf_hash
        self.idempotency_key = idempotency_key
        self.owner_id = owner_id
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        """Serializa la entidad a un diccionario para persistencia."""
        return {
            "filename": self.filename,
            "text": self.text,
            "pages": self.pages,
            "pdf_hash": self.pdf_hash,
            "idempotency_key": self.idempotency_key,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Documento":
        """Crea una entidad desde un diccionario de MongoDB."""
        return cls(
            id=str(data.get("_id")) if data.get("_id") else None,
            filename=data["filename"],
            text=data["text"],
            pages=data["pages"],
            pdf_hash=data["pdf_hash"],
            idempotency_key=data["idempotency_key"],
            owner_id=data["owner_id"],
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
        )