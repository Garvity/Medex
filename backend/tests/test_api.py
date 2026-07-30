"""Manual authenticated API smoke test.

Set FIREBASE_ID_TOKEN to an ID token issued by your Firebase Cloud project before running.
"""
import os

import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def request(method: str, path: str, payload: dict | None = None):
    token = os.environ["FIREBASE_ID_TOKEN"]
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30,
    )
    print(path, response.status_code, response.json() if response.content else None)


if __name__ == "__main__":
    request("GET", "/profile")
    request("POST", "/ask", {"query": "symptoms of gestational cholestasis", "role": "user"})
    request("GET", "/sessions")
