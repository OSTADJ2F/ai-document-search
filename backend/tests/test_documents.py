from fastapi.testclient import TestClient


def test_upload_list_get_and_delete_document(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    upload = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("notes.md", b"# Notes\n\nThe launch date is June 4.", "text/markdown")},
    )
    assert upload.status_code == 201
    document = upload.json()
    assert document["filename"] == "notes.md"
    assert document["status"] == "uploaded"

    listing = client.get("/documents", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    fetched = client.get(f"/documents/{document['id']}", headers=auth_headers)
    assert fetched.status_code == 200

    deleted = client.delete(f"/documents/{document['id']}", headers=auth_headers)
    assert deleted.status_code == 200
    assert client.get(f"/documents/{document['id']}", headers=auth_headers).status_code == 404


def test_upload_validation_and_duplicates(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert (
        client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/documents",
            headers=auth_headers,
            files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
        ).status_code
        == 415
    )
    files = {"file": ("safe.txt", b"same content", "text/plain")}
    assert client.post("/documents", headers=auth_headers, files=files).status_code == 201
    assert client.post("/documents", headers=auth_headers, files=files).status_code == 409


def test_documents_are_isolated_between_users(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    upload = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("private.txt", b"private owner data", "text/plain")},
    )
    document_id = upload.json()["id"]
    other = client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "another secure password"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert client.get(f"/documents/{document_id}", headers=other_headers).status_code == 404
    assert client.delete(f"/documents/{document_id}", headers=other_headers).status_code == 404
    assert client.get("/documents", headers=other_headers).json()["total"] == 0
