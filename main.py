from typing import Any
from fastapi import FastAPI
from pydantic import BaseModel
from doc.build import get_doc_data
from service import Service

app = FastAPI(title="Figma Doc")


class GenerateRequest(BaseModel):
    url: str
    tokens: dict[str, Any] | None = None


@app.post("/api/doc", response_model=dict[str, Any])
def get_doc(req: GenerateRequest) -> dict[str, Any]:
    return get_doc_data(Service(req.url, req.tokens).handle_doc())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
