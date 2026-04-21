from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.doc import mod_doc
from app.figma import FigmaErr, get_file, get_key, get_vars
from app.gen import add_front
from app.models import GenReq, GenRes

router = APIRouter()


@router.get("/healthz")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/generate", response_model=GenRes)
def add_gen(req: GenReq) -> GenRes:
    try:
        key = get_key(req.url)
        file_doc = get_file(key, req.token)
        var_doc, warn = get_vars(key, req.token) if req.use_vars else (None, None)
        doc = mod_doc(file_doc, var_doc)
        doc.key = key
        if warn:
            doc.warns.append(warn)
        root = Path(req.out_dir).expanduser().resolve() / key
        files = add_front(doc, root)
        return GenRes(
            file_key=key,
            file_name=doc.name,
            out_dir=str(root),
            pages=list(map(lambda item: item.route, doc.pages)),
            components=list(map(lambda item: item.tag, doc.comps)),
            files=files,
            warnings=doc.warns,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FigmaErr as exc:
        raise HTTPException(status_code=exc.code if exc.code < 500 else 502, detail=exc.msg) from exc
