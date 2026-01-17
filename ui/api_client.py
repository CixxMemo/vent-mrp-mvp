import os
from typing import Any, Dict, Optional

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


def _friendly_message(default: str, resp: requests.Response) -> str:
    try:
        data = resp.json()
        return data.get("mesaj") or data.get("detail") or default
    except Exception:
        return default


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{API_URL}{path}"
    resp = requests.get(url, params=params, timeout=10)
    if resp.ok:
        return resp.json()
    raise RuntimeError(_friendly_message("İstek başarısız oldu", resp))


def post(path: str, payload: Dict[str, Any]) -> Any:
    url = f"{API_URL}{path}"
    resp = requests.post(url, json=payload, timeout=10)
    if resp.ok:
        return resp.json()
    raise RuntimeError(_friendly_message("İstek başarısız oldu", resp))


