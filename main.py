import os
from fastapi import FastAPI
import uvicorn
from api import router
from errors import add_err


def get_app() -> FastAPI:
    app = FastAPI(title="figma-to-svelte")
    add_err(app)
    app.include_router(router)
    return app


def get_run_kw() -> dict[str, object]:
    def get_host() -> str:
        return os.environ.get("HOST", "127.0.0.1")

    def get_port() -> int:
        return int(os.environ.get("PORT", "8000"))

    return {"host": get_host(), "port": get_port()}


app = get_app()


def add_run() -> None:
    uvicorn.run(app, **get_run_kw())


if __name__ == "__main__":
    add_run()


def test_get_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_add_run(monkeypatch) -> None:
    hit: dict[str, object] = {}

    def add_fake_run(app: object, **kw: object) -> None:
        hit["app"] = app
        hit["kw"] = kw

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setattr(uvicorn, "run", add_fake_run)
    add_run()
    assert hit["app"] is app
    assert hit["kw"] == {"host": "127.0.0.1", "port": 8123}
