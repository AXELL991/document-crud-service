# Document CRUD Service

Servicio CRUD de documentos PDF extraídos. Es el único dueño de MongoDB. Es invocado por el orquestador (`export-viewer-service`).

## Responsabilidades

- Crear, leer, actualizar y eliminar documentos en MongoDB
- Garantizar idempotencia mediante `Idempotency-Key` (SHA-256 del PDF)
- Exponer endpoints paginados para listar documentos
- Validar tokens internos entre servicios

## Endpoints

Todos los endpoints requieren `X-Internal-Token`. Los endpoints de lectura/escritura por documento también requieren `X-Owner-Id`.

| Método | Ruta | Descripción | Respuesta exitosa |
|--------|------|-------------|-------------------|
| POST | `/v1/documents` | Crear documento (idempotente) | `201` |
| GET | `/v1/documents` | Listar documentos (paginado) | `200` |
| GET | `/v1/documents/{id}` | Obtener documento por ID | `200` |
| PATCH | `/v1/documents/{id}` | Actualizar parcialmente (nombre, texto) | `200` |
| DELETE | `/v1/documents/{id}` | Eliminar documento | `204` |
| GET | `/health/live` | Sonda de vitalidad | `200` |
| GET | `/health/ready` | Sonda de readiness (ping a MongoDB) | `200` |

## Arquitectura en capas

| Capa | Módulo | Responsabilidad |
|------|--------|-----------------|
| Presentación | `app/api/routes.py` | Endpoints HTTP, mapeo de errores a respuestas |
| Negocio | `app/services/document_service.py` | Reglas de negocio, orquestación de operaciones |
| Persistencia | `app/repository.py` | Acceso a MongoDB, consultas y comandos |
| Modelos | `app/models/document.py` | Entidad de dominio `Documento` |
| DTOs | `app/dtos.py` | Objetos de transferencia de datos |
| Configuración | `app/core/config.py` | Variables de entorno |
| Excepciones | `app/core/exception_handlers.py` | Manejador centralizado de excepciones |

## Variables de entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `MONGO_URI` | URI de conexión a MongoDB | `mongodb://mongo:27017/pdf_extractor_db` |
| `MONGO_DB_NAME` | Nombre de la base de datos | `pdf_extractor_db` |
| `MONGO_TIMEOUT_MS` | Timeout de conexión (ms) | `5000` |
| `INTERNAL_API_TOKEN` | Token interno para autenticación | `your-secure-token` |
| `MAX_TEXT_BYTES` | Límite de texto almacenado (bytes) | `15728640` |
| `PAGE_SIZE_MAX` | Tamaño máximo de página en listados | `100` |
| `LOGLEVEL` | Nivel de logging | `info` |

## Cómo ejecutar

### Standalone (este servicio + MongoDB)

```bash
cd document-crud-service
docker compose up --build -d
```

### Desde el orquestador (stack completo)

```bash
cd ../export-viewer-service
docker compose up --build -d
```

## Tests

```bash
uv run pytest tests/ -v
uv run ruff check app/ tests/
```

Los tests usan un repositorio en memoria (fake), por lo que no requieren una instancia de MongoDB real.

## Idempotencia

El endpoint `POST /v1/documents` acepta la cabecera `Idempotency-Key`. Si se envía la misma clave con el mismo `pdf_hash`, se devuelve el documento existente sin crear duplicados. Si la clave ya existe con un `pdf_hash` distinto, se devuelve `409 Conflict`.

## Cierre ordenado

`docker compose down -v` elimina contenedores, redes y el volumen de MongoDB.