import os

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def send_chat_message(user_id: str, message: str, language: str = "en") -> dict:
    response = requests.post(
        f"{BACKEND_URL}/api/chat",
        json={"user_id": user_id, "message": message, "language": language},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def upload_document(user_id: str, doc_type: str, file) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/api/documents/upload",
        params={"user_id": user_id, "doc_type": doc_type},
        files={"file": (file.name, file.getvalue())},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def create_gap_report(user_id: str, company_profile: dict) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/api/reports/gap-report",
        json={"user_id": user_id, "company_profile": company_profile},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()
