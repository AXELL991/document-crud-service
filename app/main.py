"""Application entry point for document-crud-service.
Provides a FastAPI app with a simple /health endpoint.
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

