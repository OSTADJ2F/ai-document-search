"""Register a demo user and upload the included sample report."""

import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
EMAIL = os.getenv("DEMO_EMAIL", "demo@example.com")
PASSWORD = os.getenv("DEMO_PASSWORD", "correct horse battery staple")


def request(path: str, payload: dict[str, str]) -> dict[str, object]:
    call = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(call) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 409 and path == "/auth/register":
            return request("/auth/login", payload)
        raise


auth = request("/auth/register", {"email": EMAIL, "password": PASSWORD})
token = str(auth["access_token"])
sample = Path(__file__).parents[2] / "docs" / "demo-risk-report.md"
boundary = f"----locus-{uuid.uuid4().hex}"
body = (
    (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="demo-risk-report.md"\r\n'
        "Content-Type: text/markdown\r\n\r\n"
    ).encode()
    + sample.read_bytes()
    + f"\r\n--{boundary}--\r\n".encode()
)
upload = urllib.request.Request(
    f"{BASE_URL}/documents",
    data=body,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
)
try:
    with urllib.request.urlopen(upload) as response:
        document = json.load(response)
except urllib.error.HTTPError as exc:
    if exc.code != 409:
        raise
    document = {"status": "already uploaded"}

print(
    json.dumps(
        {"email": EMAIL, "password": PASSWORD, "token": token, "document": document},
        indent=2,
    )
)
