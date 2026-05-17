from dataclasses import dataclass, field

type Nodes = list[TextNode | BoxNode | CompNode]


@dataclass(slots=True)
class FontDoc:
    fontFamily: str
    fontSize: float
    lineHeightPx: float
    letterSpacing: float
    fontWeight: int


@dataclass(slots=True)
class TokDoc:
    colors: dict[str, str]
    fonts: dict[str, FontDoc]
    variables: dict[str, int]


@dataclass(slots=True)
class TextNode:
    text: str
    font: str
    color: str


@dataclass(slots=True)
class Flex:
    # TODO: 定义flex可能的参数
    pass


@dataclass(slots=True)
class BoxNode:
    width: str
    height: str
    flex: Flex
    padding: list[str]
    color: str
    children: Nodes = field(default_factory=list)


@dataclass(slots=True)
class CompNode:
    props: dict[str, str]
    comp: str


@dataclass(slots=True)
class CompDoc:
    props: dict[str, str]
    roots: Nodes
    description: str = ""


@dataclass(slots=True)
class GenDoc:
    tokens: TokDoc
    comps: dict[str, CompDoc]
    pages: Nodes
