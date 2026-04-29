from typing import Any
from urllib import parse
import httpx


class FigmaErr(RuntimeError):
    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


def get_json(url: str, token: str) -> dict[str, Any]:
    try:
        res = httpx.get(
            url,
            headers={
                "X-Figma-Token": token,
                "Accept": "application/json",
            },
            timeout=30.0,
        )
        res.raise_for_status()
        return res.json()
    except httpx.HTTPStatusError as exc:
        msg = exc.response.text or exc.response.reason_phrase or "Figma API 请求失败"
        raise FigmaErr(exc.response.status_code, msg) from exc
    except httpx.RequestError as exc:
        raise FigmaErr(502, str(exc) or "无法连接 Figma API") from exc
    except ValueError as exc:
        raise FigmaErr(502, "Figma API 返回了无效 JSON") from exc


def get_file(key: str, token: str) -> dict[str, Any]:
    url = parse.urlunparse(
        (
            "https",
            "api.figma.com",
            f"/v1/files/{key}",
            "",
            parse.urlencode({"geometry": "paths"}),
            "",
        )
    )
    return get_json(url, token)
