import figma
import pytest


def test_get_key() -> None:
    url = "https://www.figma.com/design/AbCdEf123456/Test?node-id=1-2"
    assert figma.get_key(url) == "AbCdEf123456"


def test_get_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIGMA_TOKEN", " demo-token ")
    assert figma.get_token() == "demo-token"


def test_get_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIGMA_TOKEN", raising=False)
    with pytest.raises(ValueError, match="FIGMA_TOKEN"):
        figma.get_token()


def test_get_vars_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    def get_fake_json(_: str, __: str) -> dict[str, object]:
        raise figma.FigmaErr(403, "blocked")

    monkeypatch.setattr(figma, "get_json", get_fake_json)
    data, warn = figma.get_vars("demo-key", "demo-token")
    assert data is None
    assert warn is not None
    assert "variables/local" in warn
