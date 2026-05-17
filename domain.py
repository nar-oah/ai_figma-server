from dataclasses import dataclass, field


@dataclass(slots=True)
class FontDoc:
    fontFamily: str
    fontSize: float
    lineHeightPx: float
    letterSpacing: float
    fontWeight: int


@dataclass(slots=True)
class TokDoc:
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, FontDoc] = field(default_factory=dict)
    variables: dict[str, int | float | str] = field(default_factory=dict)


@dataclass(slots=True)
class TextNode:
    text: str
    font: str
    color: str


@dataclass(slots=True)
class Flex:
    direction: str = ""
    justify: str = ""
    align: str = ""
    gap: str = ""


type Node = TextNode | BoxNode | CompNode


@dataclass(slots=True)
class BoxNode:
    width: str
    height: str
    flex: Flex
    padding: list[str]
    color: str
    radius: list[str] = field(default_factory=list)
    children: list[Node] = field(default_factory=list)


@dataclass(slots=True)
class CompNode:
    props: dict[str, str]
    comp: str


@dataclass(slots=True)
class CompDoc:
    props: dict[str, str]
    roots: dict[str, list[Node]]
    description: str = ""


@dataclass(slots=True)
class GenDoc:
    tokens: TokDoc
    comps: dict[str, CompDoc]
    pages: dict[str, list[Node]]
