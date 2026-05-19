from fastapi import FastAPI, File, UploadFile
from service import Service
from json import loads

app = FastAPI(title="Figma Doc")


@app.post("/api/doc", response_model=str)
async def add_doc(url: str, file: UploadFile = File(...)) -> str:
    tokens = await file.read()
    return Service(url, loads(tokens)).add_doc()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
