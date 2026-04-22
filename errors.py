from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from figma import FigmaErr


def add_err(app: FastAPI) -> None:
    app.add_exception_handler(ValueError, get_value_err)
    app.add_exception_handler(FigmaErr, get_figma_err)


def get_value_err(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def get_figma_err(_: Request, exc: FigmaErr) -> JSONResponse:
    code = exc.code if exc.code < 500 else 502
    return JSONResponse(status_code=code, content={"detail": exc.msg})
