import json
from pathlib import Path
import pytest
import service
from models import GenReq


def test_get_gen_res(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parents[1] / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    monkeypatch.setattr(service, "get_token", lambda: "demo-token")
    monkeypatch.setattr(service, "get_file", lambda _key, _token: get_sample())
    monkeypatch.setattr(service, "get_vars", lambda _key, _token: ({"meta": {}}, "vars fallback"))
    req = GenReq(url="https://www.figma.com/design/AbCdEf123456/Test?node-id=1-2", out_dir=str(tmp_path))
    res = service.get_gen_res(req)
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
