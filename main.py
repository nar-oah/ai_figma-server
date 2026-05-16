from typing import Any
from fastapi import FastAPI
from pydantic import BaseModel
from doc.build import get_doc_data
from service import Service

app = FastAPI(title="Figma to Svelte")


class GenerateRequest(BaseModel):
    url: str
    tokens: dict[str, Any] | None = None


@app.post("/api/generate", response_model=dict[str, Any])
def add_gen(req: GenerateRequest) -> dict[str, Any]:
    doc = Service(req.url, req.tokens).handle_doc()
    return {
        "name": doc.name,
        "key": doc.key,
        "doc": get_doc_data(doc),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
