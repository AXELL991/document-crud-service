"""Fixtures compartidos para los tests del document-crud-service.

Se usa un repositorio en memoria (fake) para que los tests sean rápidos y no
requieran una instancia de MongoDB real. Se monkeypatchia ``app.repository``
antes de crear el ``TestClient`` para que el ``lifespan`` no intente conectar a
Mongo.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import app.repository as repository
from app.core.config import settings
from app.dtos import DocumentResponse, PaginatedDocuments
from app.main import app

_docs = {}
_seq = [0]


def _new_id() -> str:
    _seq[0] += 1
    return str(_seq[0])


def _make_doc(idempotency_key: str, payload) -> DocumentResponse:
    now = datetime.now(timezone.utc)
    return DocumentResponse(
        id=_new_id(),
        filename=payload.filename,
        text=payload.text,
        pages=payload.pages,
        pdf_hash=payload.pdf_hash,
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=None,
    )


async def fake_connect():
    pass


async def fake_disconnect():
    pass


async def fake_ping():
    return True


async def fake_create_document(idempotency_key: str, payload):
    if idempotency_key in _docs:
        existing = _docs[idempotency_key]
        if existing.pdf_hash == payload.pdf_hash:
            return existing
        raise repository.IdempotencyConflictError(
            f"La clave de idempotencia '{idempotency_key}' ya existe con un payload distinto"
        )
    doc = _make_doc(idempotency_key, payload)
    _docs[idempotency_key] = doc
    return doc


async def fake_get_document(doc_id: str):
    for doc in _docs.values():
        if doc.id == doc_id:
            return doc
    raise repository.DocumentNotFoundError(f"Documento {doc_id} no encontrado")


async def fake_list_documents(page: int, page_size: int):
    page_size = min(page_size, settings.page_size_max)
    items = list(_docs.values())
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]
    return PaginatedDocuments(items=page_items, total=total, page=page, page_size=page_size)


async def fake_patch_document(doc_id: str, patch):
    doc = await fake_get_document(doc_id)
    if patch.filename is not None:
        doc.filename = patch.filename
    if patch.text is not None:
        doc.text = patch.text
    doc.updated_at = datetime.now(timezone.utc)
    return doc


async def fake_delete_document(doc_id: str):
    await fake_get_document(doc_id)
    for key, doc in list(_docs.items()):
        if doc.id == doc_id:
            del _docs[key]
            return


repository.connect = fake_connect
repository.disconnect = fake_disconnect
repository.ping = fake_ping
repository.create_document = fake_create_document
repository.get_document = fake_get_document
repository.list_documents = fake_list_documents
repository.patch_document = fake_patch_document
repository.delete_document = fake_delete_document


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict:
    return {
        "X-Internal-Token": settings.internal_api_token,
        "Idempotency-Key": "test-idem-key-001",
    }


@pytest.fixture
def sample_payload() -> dict:
    return {
        "filename": "test.pdf",
        "text": "Texto de prueba extraído del PDF",
        "pages": 2,
        "pdf_hash": "abc123def456",
    }
