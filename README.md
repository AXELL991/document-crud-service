# Document CRUD Service

Servicio CRUD de documentos PDF extraídos. Es el **único dueño de MongoDB**. Es invocado por el orquestador (`export-viewer-service`).

## Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/v1/documents` | Crear documento (idempotente vía `Idempotency-Key`) | `X-Internal-Token`, `X-Owner-Id` |
| GET | `/v1/documents` | Listar documentos (paginado) | `X-Internal-Token` |
| GET | `/v1/documents/{id}` | Obtener documento por ID | `X-Internal-Token`, `X-Owner-Id` |
| PATCH | `/v1/documents/{id}` | Actualizar parcialmente | `X-Internal-Token`, `X-Owner-Id` |
| DELETE | `/v1/documents/{id}` | Eliminar documento | `X-Internal-Token`, `X-Owner-Id` |
| GET | `/health/live` | Liveness probe | — |
| GET | `/health/ready` | Readiness (ping a MongoDB) | — |

## Arquitectura

- **Base de datos:** MongoDB (único propietario, colección `documents` en `pdf_extractor_db`)
- **Idempotencia:** clave `Idempotency-Key` (SHA-256 del PDF); reenvíos seguros no duplican
- **Índices:** `idempotency_key` (único), `created_at`

## Variables de entorno

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `MONGO_URI` | `mongodb://mongo:27017/pdf_extractor_db` | URI de MongoDB |
| `MONGO_DB_NAME` | `pdf_extractor_db` | Nombre de la base de datos |
| `INTERNAL_API_TOKEN` | — | Token interno (requerido, sin default inseguro) |
| `MAX_TEXT_BYTES` | `15728640` | Límite de texto (15 MB) |
| `PAGE_SIZE_MAX` | `100` | Páginas máximas por listado |
| `LOGLEVEL` | `info` | Nivel de logging |

## Ejecución

### Standalone (solo este servicio + MongoDB)

```bash
cd document-crud-service
docker compose up --build -d
```

### Desde el orquestador (stack completo)

```bash
cd ../export-viewer-service
docker compose up --build -d
```

## Pruebas

```bash
uv run pytest tests/ -v
uv run ruff check app/ tests/
```

## Cierre ordenado

`docker compose down -v` elimina contenedores, redes y el volumen de MongoDB.