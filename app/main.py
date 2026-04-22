from __future__ import annotations
from fastapi import FastAPI
from app.api import router
from app.errors import add_err

app = FastAPI(title="figma-to-svelte")
add_err(app)
app.include_router(router)
