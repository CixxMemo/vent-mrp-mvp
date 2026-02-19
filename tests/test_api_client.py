"""Tests for API client base URL resolution."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.api_client import get_api_base_url


def test_get_api_base_url_precedence(monkeypatch):
    monkeypatch.setenv("VENTMRP_API_URL", "http://vent.example:9000")
    monkeypatch.setenv("API_URL", "http://api.example:8000")
    assert get_api_base_url() == "http://vent.example:9000"

    monkeypatch.delenv("VENTMRP_API_URL", raising=False)
    assert get_api_base_url() == "http://api.example:8000"

    monkeypatch.delenv("API_URL", raising=False)
    assert get_api_base_url() == "http://127.0.0.1:8000"
