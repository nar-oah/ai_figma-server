from __future__ import annotations
import os
import re
from typing import Any
from urllib import parse
import httpx


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


def get_token() -> str:
    token = os.environ.get("FIGMA_TOKEN", "").strip()
    if token:
        return token
    raise ValueError("缺少环境变量 FIGMA_TOKEN")


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
