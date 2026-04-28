import json
from pathlib import Path
from typing import Any
from doc import add_doc_json, mod_doc
from domain import GenDoc
from figma import get_file, get_key, get_token, get_vars
from gen import add_site
from models import GenReq, GenRes


def get_gen_res(req: GenReq) -> GenRes:
    def get_raw_data() -> tuple[str, dict[str, Any], dict[str, Any] | None, str | None]:
        key = get_key(req.url)
        token = get_token()
        file_doc = get_file(key, token)
        var_doc, warn = get_vars(key, token) if req.use_vars else (None, None)
        return key, file_doc, var_doc, warn

    def get_doc(key: str, file_doc: dict[str, Any], var_doc: dict[str, Any] | None, warn: str | None) -> GenDoc:
        doc = mod_doc(file_doc, var_doc)
        doc.key = key
        if warn:
            doc.warns.append(warn)
        return doc

    def get_out_root(key: str) -> Path:
        return Path(req.out_dir).expanduser().resolve() / key

    def add_json(path: Path, data: dict[str, Any]) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return str(path.relative_to(root))

    key, file_doc, var_doc, warn = get_raw_data()
    doc = get_doc(key, file_doc, var_doc, warn)
    root = get_out_root(key)
    files = [add_json(root / "raw" / "api_response.json", file_doc)]
    if var_doc is not None:
        files.append(add_json(root / "raw" / "variables_response.json", var_doc))
    add_doc_json(doc, root / "doc.json")
    files.append("doc.json")
    files.extend(f"web/{path}" for path in add_site(doc, root / "web"))
    return GenRes(
        file_key=key,
        file_name=doc.name,
        out_dir=str(root),
        pages=[item.route for item in doc.pages],
        components=[item.tag for item in doc.comps],
        files=files,
        warnings=doc.warns,
    )


def get_test_gen_res(tmp_path: Path, monkeypatch: Any) -> None:
    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parent / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    monkeypatch.setattr("service.get_token", lambda: "demo-token")
    monkeypatch.setattr("service.get_file", lambda _key, _token: get_sample())
    monkeypatch.setattr("service.get_vars", lambda _key, _token: ({"meta": {}}, "vars fallback"))
    req = GenReq(url="https://www.figma.com/design/AbCdEf123456/Test?node-id=1-2", out_dir=str(tmp_path))
    res = get_gen_res(req)
    root = Path(res.out_dir)
    assert root == tmp_path.resolve() / "AbCdEf123456"
    assert (root / "raw" / "api_response.json").exists()
    assert (root / "raw" / "variables_response.json").exists()
    assert (root / "doc.json").exists()
    assert (root / "web" / "src" / "lib" / "generated" / "meta.json").exists()
    assert "raw/api_response.json" in res.files
    assert "doc.json" in res.files
    assert any(path.startswith("web/") for path in res.files)
    assert res.warnings == ["vars fallback"]
