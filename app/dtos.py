"""Data Transfer Objects for document‑crud‑service.
Define simple Pydantic models – placeholder for now.
"""

from pydantic import BaseModel

class DocumentDTO(BaseModel):
    title: str
    content: str

