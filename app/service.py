from __future__ import annotations
from pathlib import Path
from app.doc import mod_doc
from app.figma import get_file, get_key, get_token, get_vars
from app.gen import add_front
from app.models import GenReq, GenRes


def get_gen_res(req: GenReq) -> GenRes:
    key = get_key(req.url)
    token = get_token()
    file_doc = get_file(key, token)
    var_doc, warn = get_vars(key, token) if req.use_vars else (None, None)
    doc = mod_doc(file_doc, var_doc)
    doc.key = key
    if warn:
        doc.warns.append(warn)
    root = get_out_root(req.out_dir, key)
    files = add_front(doc, root)
    return GenRes(
        file_key=key,
        file_name=doc.name,
        out_dir=str(root),
        pages=[item.route for item in doc.pages],
        components=[item.tag for item in doc.comps],
        files=files,
        warnings=doc.warns,
    )


def get_out_root(out_dir: str, key: str) -> Path:
    return Path(out_dir).expanduser().resolve() / key
