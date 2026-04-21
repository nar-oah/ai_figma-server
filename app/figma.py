from __future__ import annotations
import json
import re
from typing import Any
from urllib import error, parse, request


class FigmaErr(RuntimeError):
    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


def get_key(url: str) -> str:
    hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
    if hit:
        return hit.group(1)
    raise ValueError("无法从链接中提取 Figma file key")


def get_json(url: str, token: str) -> dict[str, Any]:
    req = request.Request(
        url,
        headers={
            "X-Figma-Token": token,
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as res:
            body = res.read().decode("utf-8")
            return json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        msg = body or exc.reason or "Figma API 请求失败"
        raise FigmaErr(exc.code, msg) from exc
    except error.URLError as exc:
        raise FigmaErr(502, str(exc.reason) or "无法连接 Figma API") from exc


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


def get_vars(key: str, token: str) -> tuple[dict[str, Any] | None, str | None]:
    url = parse.urlunparse(
        (
            "https",
            "api.figma.com",
            f"/v1/files/{key}/variables/local",
            "",
            "",
            "",
        )
    )
    try:
        return get_json(url, token), None
    except FigmaErr as exc:
        if exc.code in {401, 403, 404}:
            return None, f"variables/local 未返回可用数据，已退回样式与绑定值推断: {exc.msg}"
        raise
