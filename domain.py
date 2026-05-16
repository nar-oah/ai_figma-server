from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TokenValueDoc:
    name: str
    kind: str
    css_name: str
    css_value: str
    value: Any
    ref: str | None = None


@dataclass(slots=True)
class TokDoc:
    root: dict[str, str] = field(default_factory=dict)
    classes: dict[str, str] = field(default_factory=dict)
    paint: dict[str, str] = field(default_factory=dict)
    text: dict[str, str] = field(default_factory=dict)
    var: dict[str, str] = field(default_factory=dict)
    colors: list[TokenValueDoc] = field(default_factory=list)
    fonts: list[TokenValueDoc] = field(default_factory=list)
    variables: list[TokenValueDoc] = field(default_factory=list)


@dataclass(slots=True)
class PropDoc:
    raw: str
    name: str
    kind: str
    default: str
    options: list[str] = field(default_factory=list)


@dataclass(slots=True)
class NodeDoc:
    kind: str
    tag: str
    name: str
    classes: list[str] = field(default_factory=list)
    attrs: list[tuple[str, object]] = field(default_factory=list)
    text: str | None = None
    expr: str | None = None
    comp: str | None = None
    raw: str | None = None
    children: list["NodeDoc"] = field(default_factory=list)


@dataclass(slots=True)
class VariantDoc:
    name: str
    when: dict[str, str]
    root: NodeDoc


@dataclass(slots=True)
class CompDoc:
    name: str
    tag: str
    props: list[PropDoc]
    variants: list[VariantDoc]
    description: str = ""
    meta: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class PageDoc:
    name: str
    route: str
    root: NodeDoc


@dataclass(slots=True)
class RefDoc:
    tag: str
    prop: dict[str, str]


@dataclass(slots=True)
class GenDoc:
    key: str
    name: str
    tokens: TokDoc
    comps: list[CompDoc]
    pages: list[PageDoc]
    warns: list[str] = field(default_factory=list)
