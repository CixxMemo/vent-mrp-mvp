import os
from typing import Any, Dict, Optional

import requests

BACKEND_DOWN_MESSAGE = "Backend is not running. Please start the app using run_app.py (or the packaged launcher)."


def get_api_base_url() -> str:
    return os.getenv("VENTMRP_API_URL") or os.getenv("API_URL") or "http://127.0.0.1:8000"


def _friendly_message(default: str, resp: requests.Response) -> str:
    try:
        data = resp.json()
        return data.get("mesaj") or data.get("detail") or default
    except Exception:
        return default


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
    url = f"{get_api_base_url()}{path}"
    try:
        return requests.request(method=method, url=url, timeout=10, **kwargs)
    except requests.RequestException as exc:
        raise RuntimeError(BACKEND_DOWN_MESSAGE) from exc


def get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    resp = _request("GET", path, params=params)
    if resp.ok:
        return resp.json()
    raise RuntimeError(_friendly_message("İstek başarısız oldu", resp))


def post(path: str, payload: Dict[str, Any]) -> Any:
    resp = _request("POST", path, json=payload)
    if resp.ok:
        return resp.json()
    raise RuntimeError(_friendly_message("İstek başarısız oldu", resp))


