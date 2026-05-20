# figma-doc

FastAPI 服务。输入 Figma 链接和导出的 token JSON，读取环境变量 `FIGMA_TOKEN` 拉取文件数据，清洗成内部 `GenDoc` 数据后写入 PostgreSQL，并返回用于定位数据的 token。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FIGMA_TOKEN="<figma_token>"
export PGDATABASE="figma"
python main.py
```

也可以用：

```bash
uvicorn main:app --reload
```

默认监听 `127.0.0.1:8000`。可以通过 `HOST` 和 `PORT` 环境变量覆盖。

## 接口

### `POST /api/doc`

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
  }
}
```

响应只返回生成的定位 token。`tokens` 对应 Figma 导出的类似 `tokens.json` 的 JSON 内容。数据库连接使用 `psycopg.connect()` 无参数读取 `PGHOST`、`PGPORT`、`PGDATABASE`、`PGUSER`、`PGPASSWORD` 等环境变量。

建表 SQL 位于 `schema.sql`，需要在 `figma` 数据库中先执行。

## 输出结构

正式接口不写文件。`output/api_response.json` 是本地样例输入，`python doc/build.py` 会写排查用 `output/doc.json`。

```text
output/
├── api_response.json     # only when running service.py
├── doc.json              # only when running doc/build.py
└── token.json              # only when running doc/build.py
```

## 代码结构

```text
.
├── domain.py
├── main.py
├── service.py
├── doc/
│   ├── build.py
│   └── tokens.py
├── output/
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

## 语义约定

`TokDoc` 保存全局颜色、字体、变量的名字和值。节点中的 `width`、`height`、`padding`、`color`、`font` 只引用这些名字，不写具体值。

Figma API 能稳定给出布局、层级、样式、变量绑定、组件 props 和实例选项，但不能可靠推断业务语义。比如 `reverse` 是否只是反转颜色、某个 frame 应该是 `button` 还是 `input`，都不在当前清洗层处理。
