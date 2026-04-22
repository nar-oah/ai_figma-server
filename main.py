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
