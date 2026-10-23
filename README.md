# Document CRUD Service

## Directory layout

```
document-crud-service/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ core/
│  │   ├─ __init__.py
│  │   ├─ config.py
│  │   ├─ logging_config.py
│  │   ├─ metrics.py
│  │   └─ exception_handlers.py
│  ├─ api/
│  │   ├─ __init__.py
│  │   └─ routes.py
│  ├─ dtos.py
│  ├─ exceptions.py
│  └─ repository.py
├─ tests/
│  ├─ __init__.py
│  ├─ conftest.py
│  └─ test_document_crud.py
├─ Dockerfile
├─ build.sh
└─ pyproject.toml
```