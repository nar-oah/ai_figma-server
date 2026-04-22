# figma-to-svelte

FastAPI 服务。输入 Figma 设计稿链接，读取环境变量 `FIGMA_TOKEN`，调用官方 `GET /v1/files/:key` 与可选的 `GET /v1/files/:key/variables/local`，把页面树、组件树、样式和变量绑定整理成中间文档，再生成 Svelte + UnoCSS 代码。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FIGMA_TOKEN="<figma_token>"
uvicorn app.main:app --reload
```

## 接口

### `GET /healthz`

健康检查接口，返回：

```json
{
  "status": "ok"
}
```

### `POST /api/generate`

请求体：

```json
{
  "url": "https://www.figma.com/design/<file_key>/<file_name>",
  "out_dir": "generated",
  "use_vars": true
}
```

返回值会给出：

- Figma 文件 key 和名称
- 实际输出目录
- 识别到的页面路由
- 生成出的组件名
- 写入的文件列表
- 变量接口降级等告警信息

## 处理流程

1. `app/main.py` 创建 FastAPI 应用，注册异常处理器和路由。
2. `app/api.py` 负责 HTTP 层，把请求转给服务函数。
3. `app/service.py` 组织完整生成流程：解析链接、读取 Token、拉取 Figma 数据、构建文档、写出前端文件。
4. `app/figma.py` 负责与 Figma API 通信。
5. `app/doc*.py` 系列模块把 Figma 原始 JSON 转成内部 `GenDoc` 文档。
6. `app/gen*.py` 系列模块把 `GenDoc` 渲染成 Svelte、UnoCSS 和元数据文件。

## 代码结构

```text
.
├── README.md
├── requirements.txt
├── api_response.json
├── app/
│   ├── api.py
│   ├── doc.py
│   ├── doc_class.py
│   ├── doc_class_layout.py
│   ├── doc_class_style.py
│   ├── doc_css.py
│   ├── doc_name.py
│   ├── doc_node.py
│   ├── doc_prop.py
│   ├── doc_svg.py
│   ├── doc_token.py
│   ├── doc_var.py
│   ├── doc_walk.py
│   ├── domain.py
│   ├── errors.py
│   ├── figma.py
│   ├── gen.py
│   ├── gen_node.py
│   ├── gen_static.py
│   ├── gen_svelte.py
│   ├── main.py
│   ├── models.py
│   └── service.py
└── tests/
    ├── output/
    └── test_flow.py
```

## 文件与目录说明

### 根目录

| 路径 | 作用 |
| --- | --- |
| `README.md` | 项目说明、接口说明、代码结构索引。 |
| `requirements.txt` | Python 依赖清单。 |
| `api_response.json` | Figma API 示例响应，供测试和本地回归使用。 |
| `app/` | 后端源码目录。 |
| `tests/` | 测试目录。 |
| `.git/` | Git 仓库元数据目录，不属于业务代码。 |
| `.pytest_cache/` | pytest 运行缓存目录，可忽略。 |
| `.venv/` | 当前项目常用虚拟环境目录，本地环境文件。 |
| `venv/` | 另一个本地虚拟环境目录，通常是历史残留或备用环境。 |

### `app/` 源码目录

| 路径 | 作用 |
| --- | --- |
| `app/main.py` | FastAPI 入口，创建应用并注册异常处理器、路由。 |
| `app/api.py` | API 路由层，仅保留 HTTP 接口定义。 |
| `app/service.py` | 生成流程编排层，负责串起抓取、转换、落盘。 |
| `app/errors.py` | 全局异常映射，把 `ValueError` 和 `FigmaErr` 转成 HTTP 响应。 |
| `app/models.py` | Pydantic 请求/响应模型。 |
| `app/domain.py` | 项目核心 dataclass 文档模型，如 `GenDoc`、`NodeDoc`、`CompDoc`。 |
| `app/figma.py` | Figma 链接解析、环境变量读取、HTTP 请求和错误封装。 |
| `app/doc.py` | 原始 Figma 文档转内部文档的总入口。 |
| `app/doc_prop.py` | 组件属性、组件引用映射、组件变体文档组装。 |
| `app/doc_node.py` | 通用节点转换，负责实例节点、文本节点、普通容器节点。 |
| `app/doc_svg.py` | 向量节点和 SVG path 片段生成。 |
| `app/doc_css.py` | 颜色、描边、数值、变量引用对应的 CSS 值推导。 |
| `app/doc_token.py` | 文本 token、颜色 token、变量 token 汇总。 |
| `app/doc_var.py` | Figma Variables 元数据解析和变量值回退逻辑。 |
| `app/doc_class.py` | 节点类名聚合入口，把各类 class 规则合并。 |
| `app/doc_class_layout.py` | 布局相关类名，如 flex、gap、padding、尺寸、自适应。 |
| `app/doc_class_style.py` | 视觉样式相关类名，如背景、边框、圆角、文字、旋转。 |
| `app/doc_name.py` | slug、PascalCase、属性名、像素文本等命名工具。 |
| `app/doc_walk.py` | 节点遍历、嵌套字段读取、变量引用扁平化等底层访问工具。 |
| `app/gen.py` | 前端文件落盘入口，组织最终输出文件表。 |
| `app/gen_static.py` | 生成静态文件内容，如 `uno.config.ts`、`app.css`、`meta.json`。 |
| `app/gen_svelte.py` | 组件页与页面级 Svelte 文件拼装。 |
| `app/gen_node.py` | 单个节点的 Svelte 标记渲染、属性和 class 输出。 |
| `app/__pycache__/` | Python 字节码缓存目录，可忽略。 |

### `tests/` 测试目录

| 路径 | 作用 |
| --- | --- |
| `tests/test_flow.py` | 主流程回归测试，覆盖链接解析、Token 读取、文档转换和文件生成。 |
| `tests/output/` | 手动检查或测试输出文件时可使用的目录。 |
| `tests/__pycache__/` | Python 字节码缓存目录，可忽略。 |

### 本地工具目录

| 路径 | 作用 |
| --- | --- |
| `.git/hooks/` | Git hook 脚本目录。 |
| `.git/info/` | Git 本地附加信息目录。 |
| `.git/logs/` | Git reflog 目录。 |
| `.git/objects/` | Git 对象数据库目录。 |
| `.git/refs/` | Git 分支、标签引用目录。 |
| `.pytest_cache/v/` | pytest 版本缓存子目录。 |
| `.venv/bin/` | 当前虚拟环境可执行文件目录。 |
| `.venv/include/` | 当前虚拟环境头文件目录。 |
| `.venv/lib/` | 当前虚拟环境库目录。 |
| `venv/bin/` | 备用虚拟环境可执行文件目录。 |
| `venv/include/` | 备用虚拟环境头文件目录。 |
| `venv/lib/` | 备用虚拟环境库目录。 |

## 生成结果

默认会在 `<out_dir>/<file_key>/` 下生成：

- `uno.config.ts`：UnoCSS 配置和 token 注入入口
- `src/app.css`：应用级基础样式
- `src/routes/+layout.svelte`：Svelte 根布局
- `src/routes/generated/<page>/+page.svelte`：页面级输出
- `src/lib/generated/components/*.svelte`：组件级输出
- `src/lib/generated/meta.json`：页面、组件、告警信息元数据

## 当前代码分层建议

- 如果你要看接口行为，从 `app/main.py -> app/api.py -> app/service.py` 开始。
- 如果你要看 Figma 原始数据怎么变成中间结构，从 `app/doc.py` 开始，再往 `doc_prop.py`、`doc_node.py`、`doc_css.py` 追。
- 如果你要看最终 Svelte 文件怎么拼，从 `app/gen.py -> app/gen_svelte.py -> app/gen_node.py` 开始。
