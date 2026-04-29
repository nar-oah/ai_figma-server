from fastapi import FastAPI
from models import GenReq, GenRes
from service import get_gen_res

app = FastAPI(title="Figme to Svelte")


@app.post("/api/generate", response_model=GenRes)
def add_gen(req: GenReq) -> GenRes:
    return get_gen_res(req)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
