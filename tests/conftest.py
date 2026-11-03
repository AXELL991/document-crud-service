"""
Fixtures compartidos para los tests del document-crud-service.

Se usa un repositorio falso (fake) para que los tests sean rápidos y no
requieran una instancia de MongoDB real. Se monkeypatchia
``app.main.repository`` y ``app.main.document_service`` antes de crear el
``TestClient`` para que el ``lifespan`` use el fake en lugar de conectar a Mongo.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.core.config import settings
from app.dtos import PaginatedDocuments
from app.exceptions import DocumentNotFoundError, IdempotencyConflictError
from app.models.document import Documento
from app.repository import DocumentRepository
from app.services.document_service import DocumentService


_docs: dict[str, Documento] = {}
_seq = [0]


def _new_id() -> str:
    _seq[0] += 1
    return str(_seq[0])


class FakeDocumentRepository(DocumentRepository):
    """Repositorio falso para tests."""

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def ping(self):
        return True

    async def create(self, idempotency_key: str, documento: Documento) -> Documento:
        if idempotency_key in _docs:
            existing = _docs[idempotency_key]
            if existing.pdf_hash == documento.pdf_hash:
                return existing
            raise IdempotencyConflictError(
                f"La clave de idempotencia '{idempotency_key}' ya existe con un payload distinto"
            )
        documento.id = _new_id()
        _docs[idempotency_key] = documento
        return documento

    async def get_by_id(self, doc_id: str, owner_id: str) -> Documento:
        for doc in _docs.values():
            if doc.id == doc_id and doc.owner_id == owner_id:
                return doc
        raise DocumentNotFoundError(f"Documento {doc_id} no encontrado")

    async def get_by_checksum(self, checksum: str, owner_id: str) -> Documento:
        for doc in _docs.values():
            if doc.pdf_hash == checksum and doc.owner_id == owner_id:
                return doc
        raise DocumentNotFoundError(f"Documento con checksum {checksum} no encontrado")

    async def list(self, page: int, page_size: int) -> PaginatedDocuments:
        page_size = min(page_size, settings.page_size_max)
        items = list(_docs.values())
        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]
        from app.dtos import DocumentResponse
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
                for d in page_items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(self, doc_id: str, owner_id: str, patch) -> Documento:
        doc = await self.get_by_id(doc_id, owner_id)
        if patch.filename is not None:
            doc.filename = patch.filename
        if patch.text is not None:
            doc.text = patch.text
        doc.updated_at = datetime.now(timezone.utc)
        return doc

    async def delete(self, doc_id: str, owner_id: str) -> None:
        await self.get_by_id(doc_id, owner_id)
        for key, doc in list(_docs.items()):
            if doc.id == doc_id:
                del _docs[key]
                return


@pytest.fixture(autouse=True)
def _inject_fake_repository():
    """Inyecta el repositorio falso en el módulo principal antes del lifespan."""
    fake = FakeDocumentRepository()
    main_module.repository = fake
    main_module.document_service = DocumentService(repository=fake)
    _docs.clear()
    _seq[0] = 0
    yield
    _docs.clear()
    _seq[0] = 0


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict:
    return {
        "X-Internal-Token": settings.internal_api_token,
        "Idempotency-Key": "test-idem-key-001",
        "X-Owner-Id": "test-owner-001",
    }


@pytest.fixture
def sample_payload() -> dict:
    return {
        "filename": "test.pdf",
        "text": "Texto de prueba extraído del PDF",
        "pages": 2,
        "pdf_hash": "abc123def456",
        "owner_id": "test-owner-001",
    }