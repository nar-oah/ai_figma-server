from typing import Any
from fastapi.testclient import TestClient
import pytest
import main


def test_get_health() -> None:
    client = TestClient(main.app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_add_run(monkeypatch: pytest.MonkeyPatch) -> None:
    hit: dict[str, object] = {}

    def add_fake_run(app: object, **kw: Any) -> None:
        hit["app"] = app
        hit["kw"] = kw

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setattr(main.uvicorn, "run", add_fake_run)
    main.add_run()
    assert hit["app"] is main.app
    assert hit["kw"] == {"host": "127.0.0.1", "port": 8123}
