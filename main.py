from fastapi import Body, FastAPI
from service import GenRes, get_gen_res

app = FastAPI(title="Figme to Svelte")


@app.post("/api/generate", response_model=GenRes)
def add_gen(url: str = Body(..., embed=True)) -> GenRes:
    return get_gen_res(url)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
