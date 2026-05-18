from fastapi import FastAPI, File, UploadFile
from domain import GenDoc
from service import Service
from json import loads

app = FastAPI(title="Figma Doc")


@app.post("/api/doc", response_model=GenDoc)
async def get_doc(url: str, file: UploadFile = File(...)) -> GenDoc:
    tokens = await file.read()
    return Service(url, loads(tokens)).get_doc()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
