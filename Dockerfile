FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build tools for uv (if needed)
COPY pyproject.toml .

# Copy source code
COPY . .

RUN pip install --no-cache-dir .[dev]

EXPOSE 8000

# Export the FastAPI app (module name may vary – adjust if needed)
CMD ["uvicorn", "app.repository:app", "--host", "0.0.0.0", "--port", "8000"]
