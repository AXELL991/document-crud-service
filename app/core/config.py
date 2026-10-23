"""Core configuration for document‑crud‑service.
All settings are read from environment variables (Twelve‑Factor).
"""
import os

# Logging level (default INFO)
LOGLEVEL = os.getenv("LOGLEVEL", "INFO")

# Mongo connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pdf_extractor_db")

# Docker resource limits (informative, not enforced here)
CPU_LIMIT = os.getenv("CPU_LIMIT", "1")
MEMORY_LIMIT = os.getenv("MEMORY_LIMIT", "512m")

