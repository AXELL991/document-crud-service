"""Métricas Prometheus para document-crud-service."""
from prometheus_client import Counter, Histogram

crud_operations = Counter(
    "document_crud_operations_total",
    "Operaciones CRUD por tipo",
    labelnames=["operation"],
)

crud_duration = Histogram(
    "document_crud_duration_seconds",
    "Duración de operaciones CRUD",
    labelnames=["operation"],
)
