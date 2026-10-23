# Contract – Document CRUD Service

## Overview
A stateful FastAPI service that is the **sole owner of the MongoDB database**. It provides full CRUD operations for processed PDF documents, validates checksums, prevents duplicates, and returns uniform error responses.

---

## Endpoints
| Method | Path | Description | Request | Response | Errors |
|--------|------|-------------|---------|----------|--------|
| **POST** | `/documentos` | Create a new document record (used internally by the orchestrator). | `application/json` with fields `archivo`, `texto`, `hash_seguridad` | `201 Created` `UploadResponse` (status, message, filename, sha256) | `409 Conflict` – duplicate checksum. <br> `400 Bad Request` – validation error. |
| **GET** | `/documentos` | List all stored documents. | – | `200 OK` `ListaDocumentosResponse` (total, documentos) | – |
| **GET** | `/documentos/{checksum}` | Retrieve a single document by its SHA‑256 checksum. | – | `200 OK` `DocumentoResponse` (archivo, texto, hash_seguridad) | `404 Not Found` – not present. |
| **PUT** | `/documentos/{checksum}` | Update the filename of an existing document. | `application/json` `ActualizarRequest` (nuevo_nombre) | `200 OK` `MensajeResponse` (status, message) | `404 Not Found` – checksum missing. <br> `400 Bad Request` – invalid name. |
| **DELETE** | `/documentos/{checksum}` | Delete a document from the database. | – | `200 OK` `MensajeResponse` | `404 Not Found` – checksum missing. |
| **GET** | `/health` | Health check that includes MongoDB connectivity. | – | `200 OK` (healthy) or `503 Service Unavailable` (DB down) |
| **GET** | `/metrics` | Prometheus‑compatible metrics endpoint (optional). | – | `200 OK` plain‑text metrics |

---

## Non‑functional Requirements (NFRs)
- **Persistence**: Uses MongoDB (service name `mongo` inside Docker network). Connection string via `MONGO_URI` and DB name via `MONGO_DB_NAME` env vars.
- **Idempotency**: Duplicate detection based on `hash_seguridad`. Returns **409** on conflict.
- **Logging**: JSON logs to stdout, level controlled by `LOGLEVEL`.
- **Configuration**: All settings via environment variables (`MONGO_URI`, `MONGO_DB_NAME`, `LOGLEVEL`, etc.) following Twelve‑Factor.
- **Security**: Uniform error payload `{ "error": "<code>", "message": "<text>" }` for all HTTP errors.
- **Rate limiting**: Global limiter defined in `core/rate_limit.py` (e.g., 60/minute for read ops, 5/minute for writes).
- **Docker resources**: Container limited to **1 CPU** and **512 MiB–1 GiB** RAM.

---

## Contracts (JSON Schema snippets)
```json
// UploadResponse
{ "type": "object", "properties": { "status": { "type": "string" }, "message": { "type": "string" }, "filename": { "type": "string" }, "sha256": { "type": "string" } }, "required": ["status","message","filename","sha256"] }

// ListaDocumentosResponse
{ "type": "object", "properties": { "total": { "type": "integer" }, "documentos": { "type": "array", "items": { "$ref": "#/components/schemas/DocumentoResponse" } } }, "required": ["total","documentos"] }

// DocumentoResponse
{ "type": "object", "properties": { "archivo": { "type": "string" }, "texto": { "type": "string" }, "hash_seguridad": { "type": "string" } }, "required": ["archivo","texto","hash_seguridad"] }

// MensajeResponse
{ "type": "object", "properties": { "status": { "type": "string" }, "message": { "type": "string" } }, "required": ["status","message"] }

// ActualizarRequest
{ "type": "object", "properties": { "nuevo_nombre": { "type": "string" } }, "required": ["nuevo_nombre"] }
```

---

*Document version*: 1.0 – **2026‑10‑22**
