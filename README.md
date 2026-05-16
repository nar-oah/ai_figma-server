# figma-to-svelte

FastAPI 服务。输入 Figma 链接和导出的 token JSON，读取环境变量 `FIGMA_TOKEN` 拉取文件数据，并清洗成内部 `GenDoc` 数据。`doc.json` 是测试和排查用副产物，正式接口默认只返回 doc 数据；需要机械生成 Svelte + UnoCSS 时再开启 `emit_code`。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FIGMA_TOKEN="<figma_token>"
python main.py
```

也可以用：

```bash
uvicorn main:app --reload
```

默认监听 `127.0.0.1:8000`。可以通过 `HOST` 和 `PORT` 环境变量覆盖。

## 接口

### `GET /healthz`

返回：

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
  "tokens": {
    "input-width": {
      "$type": "number",
      "$value": 393,
      "$extensions": {
        "com.figma.variableId": "VariableID:2001:237"
      }
    }
  },
  "emit_code": false
}
```

响应会返回文件 key、文件名、输出目录、写入文件列表和清洗后的 doc。`tokens` 对应 Figma 导出的类似 `Mode 1.tokens.json` 的 JSON 内容。

## 输出结构

正式运行不写 `doc.json`。测试会读取 `output/samples/api_response.json` 和 token JSON，并把排查用 doc 写到 `output/doc.json`。

开启 `emit_code` 后，生成代码直接写到 `output/`：

```text
output/
├── samples/
│   └── api_response.json
├── doc.json              # only tests/debug
├── uno.config.ts         # only when emit_code=true
└── src/                  # only when emit_code=true
```

## 代码结构

```text
.
├── api.py
├── domain.py
├── errors.py
├── figma.py
├── main.py
├── service.py
├── doc/
│   ├── build.py
│   ├── class_layout.py
│   ├── class_style.py
│   ├── classes.py
│   ├── components.py
│   ├── css.py
│   ├── meta.py
│   ├── names.py
│   ├── node.py
│   ├── pages.py
│   ├── props.py
│   ├── style_tokens.py
│   ├── svg.py
│   ├── token_file.py
│   ├── tokens.py
│   ├── vars.py
│   └── walk.py
├── gen/
│   ├── node.py
│   ├── static.py
│   ├── svelte.py
│   └── write.py
├── output/
│   └── samples/
```

## 模块运行

启动后端服务：

```bash
python main.py
```

仅拉取并保存原始 API 响应：

```bash
FIGMA_TOKEN="<figma_token>" python service.py "https://www.figma.com/design/<file_key>/<file_name>"
```

用 sample JSON 生成排查用 doc：

```bash
python doc/build.py
```

用 sample JSON 机械生成代码：

```bash
python gen/write.py
```

## 语义约定

Figma API 能稳定给出布局、层级、样式、变量绑定、组件 props 和实例选项，但不能可靠推断业务语义。比如 `reverse` 是否只是反转颜色、某个 frame 应该是 `button` 还是 `input`，都需要设计稿显式携带规则。

建议在 component set description 中加入结构化元数据，例如：

```text
@code {"tag":"button","emits":["is_click"],"props":{"reverse":{"role":"theme"}}}
```

当前清洗阶段会保留组件 description，并尝试解析 description 中的 JSON / fenced JSON / `@code {...}` 到 `CompDoc.meta`，供后续 AI 或更严格的生成器使用。
