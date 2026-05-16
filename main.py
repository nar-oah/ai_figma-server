from typing import Any
from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel, Field
from doc.build import get_doc_data
from gen.write import add_site
from service import Service

app = FastAPI(title="Figma to Svelte")


class GenerateRequest(BaseModel):
    url: str
    tokens: dict[str, Any] | None = None
    emit_code: bool = Field(default=False)


@app.post("/api/generate", response_model=dict[str, Any])
def add_gen(req: GenerateRequest) -> dict[str, Any]:
    doc = Service(req.url, req.tokens).handle_doc()
    files = add_site(doc, Path("output")) if req.emit_code else []
    return {
        "name": doc.name,
        "key": doc.key,
        "output": "output",
        "files": files,
        "doc": get_doc_data(doc),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
