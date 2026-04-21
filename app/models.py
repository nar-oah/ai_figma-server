from __future__ import annotations
from pydantic import BaseModel, Field


class GenReq(BaseModel):
    url: str
    token: str
    out_dir: str = "generated"
    use_vars: bool = True


class GenRes(BaseModel):
    file_key: str
    file_name: str
    out_dir: str
    pages: list[str]
    components: list[str]
    files: list[str]
    warnings: list[str] = Field(default_factory=list)
