"""Routes for document‑crud‑service.
Provides placeholder CRUD endpoints for a generic Document model.
"""

from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter(prefix="/documents", tags=["documents"])

# In‑memory placeholder storage
_fake_db: List[dict] = []

@router.post("/", response_model=dict)
async def create_document(doc: dict):
    _fake_db.append(doc)
    return doc

@router.get("/", response_model=List[dict])
async def list_documents():
    return _fake_db

@router.get("/{doc_id}", response_model=dict)
async def get_document(doc_id: int):
    try:
        return _fake_db[doc_id]
    except IndexError:
        raise HTTPException(status_code=404, detail="Document not found")

@router.put("/{doc_id}", response_model=dict)
async def update_document(doc_id: int, doc: dict):
    try:
        _fake_db[doc_id] = doc
        return doc
    except IndexError:
        raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{doc_id}", response_model=dict)
async def delete_document(doc_id: int):
    try:
        removed = _fake_db.pop(doc_id)
        return removed
    except IndexError:
        raise HTTPException(status_code=404, detail="Document not found")

