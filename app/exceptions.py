"""Excepciones de dominio del document-crud-service."""


class DocumentNotFoundError(Exception):
    """El documento solicitado no existe."""


class IdempotencyConflictError(Exception):
    """Misma clave de idempotencia con payload distinto."""


class TextTooLargeError(Exception):
    """El texto supera el límite MAX_TEXT_BYTES."""
