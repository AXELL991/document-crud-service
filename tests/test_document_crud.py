"""Tests del document-crud-service (repositorio en memoria, sin Mongo real)."""
from fastapi.testclient import TestClient


def test_health_live(client: TestClient):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_no_token_returns_401(client: TestClient, sample_payload: dict):
    r = client.post(
        "/v1/documents",
        json=sample_payload,
        headers={"Idempotency-Key": "key-001"},
    )
    assert r.status_code == 401


def test_create_and_get_document(client: TestClient, auth_headers: dict, sample_payload: dict):
    r = client.post("/v1/documents", json=sample_payload, headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["filename"] == sample_payload["filename"]
    assert body["text"] == sample_payload["text"]
    assert body["pages"] == sample_payload["pages"]
    doc_id = body["id"]

    r = client.get(
        f"/v1/documents/{doc_id}",
        headers={"X-Internal-Token": auth_headers["X-Internal-Token"]},
    )
    assert r.status_code == 200
    assert r.json()["id"] == doc_id


def test_idempotency_same_payload_returns_existing(
    client: TestClient, sample_payload: dict
):
    headers = {
        "X-Internal-Token": "change-me",
        "Idempotency-Key": "idem-same-001",
    }
    r1 = client.post("/v1/documents", json=sample_payload, headers=headers)
    assert r1.status_code == 201, r1.text
    id1 = r1.json()["id"]

    # Misma clave y mismo payload -> devuelve el existente (no crea duplicado).
    # Nota: el decorador de la ruta fija status 201; lo importante es el id.
    r2 = client.post("/v1/documents", json=sample_payload, headers=headers)
    assert r2.status_code == 201, r2.text
    assert r2.json()["id"] == id1


def test_idempotency_same_key_diff_payload_returns_409(
    client: TestClient, sample_payload: dict
):
    headers = {
        "X-Internal-Token": "change-me",
        "Idempotency-Key": "idem-diff-001",
    }
    client.post("/v1/documents", json=sample_payload, headers=headers)

    different = dict(sample_payload, text="Otro texto distinto", pdf_hash="otro-hash-789")
    r = client.post("/v1/documents", json=different, headers=headers)
    assert r.status_code == 409, r.text


def test_list_documents(client: TestClient, auth_headers: dict, sample_payload: dict):
    client.post("/v1/documents", json=sample_payload, headers=auth_headers)
    r = client.get(
        "/v1/documents",
        headers={"X-Internal-Token": auth_headers["X-Internal-Token"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1


def test_get_nonexistent_document(client: TestClient, auth_headers: dict):
    r = client.get(
        "/v1/documents/000000000000000000000000",
        headers={"X-Internal-Token": auth_headers["X-Internal-Token"]},
    )
    assert r.status_code == 404


def test_patch_document(client: TestClient, auth_headers: dict, sample_payload: dict):
    r = client.post("/v1/documents", json=sample_payload, headers=auth_headers)
    assert r.status_code == 201
    doc_id = r.json()["id"]

    r = client.patch(
        f"/v1/documents/{doc_id}",
        json={"filename": "renombrado.pdf"},
        headers={
            "X-Internal-Token": auth_headers["X-Internal-Token"],
            "Idempotency-Key": "patch-key-001",
        },
    )
    assert r.status_code == 200
    assert r.json()["filename"] == "renombrado.pdf"


def test_delete_document(client: TestClient, auth_headers: dict, sample_payload: dict):
    r = client.post("/v1/documents", json=sample_payload, headers=auth_headers)
    assert r.status_code == 201
    doc_id = r.json()["id"]

    r = client.delete(
        f"/v1/documents/{doc_id}",
        headers={"X-Internal-Token": auth_headers["X-Internal-Token"]},
    )
    assert r.status_code == 204, r.text

    r = client.get(
        f"/v1/documents/{doc_id}",
        headers={"X-Internal-Token": auth_headers["X-Internal-Token"]},
    )
    assert r.status_code == 404
