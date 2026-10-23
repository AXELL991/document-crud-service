"""Metrics utilities for document‑crud‑service.
Placeholder – replace with real Prometheus metrics.
"""

from prometheus_client import Counter

requests_total = Counter('document_crud_requests_total', 'Total requests')

