# figma-to-svelte

FastAPI 服务。输入 Figma 链接，读取环境变量 `FIGMA_TOKEN`，拉取文件数据和可选变量数据，先清洗成内部文档，再生成 Svelte + UnoCSS 代码，并把各阶段产物统一写进 `output/`。

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
  "out_dir": "output/runs",
  "use_vars": true
}
```

响应会返回文件 key、文件名、输出目录、页面路由、组件名、写入文件列表和告警信息。

## 输出结构

所有运行产物统一写到 `output/` 下：

```text
output/
├── samples/
│   └── api_response.json
└── runs/
    └── <file_key>/
        ├── raw/
        │   ├── api_response.json
        │   └── variables_response.json
        ├── doc.json
        └── web/
            ├── uno.config.ts
            └── src/
```

## 代码结构

```text
.
├── api.py
├── domain.py
├── errors.py
├── figma.py
├── main.py
├── models.py
├── service.py
├── doc/
│   ├── build.py
│   ├── class_layout.py
│   ├── class_style.py
│   ├── classes.py
│   ├── css.py
│   ├── names.py
│   ├── node.py
│   ├── props.py
│   ├── svg.py
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
└── tests/
    ├── doc/
    │   └── test_build.py
    ├── gen/
    │   └── test_write.py
    ├── test_figma.py
    ├── test_main.py
    └── test_service.py
```

## 模块测试

按节点排查时可以直接跑对应测试：

```bash
./.venv/bin/pytest tests/test_main.py
./.venv/bin/pytest tests/test_figma.py
./.venv/bin/pytest tests/doc/test_build.py
./.venv/bin/pytest tests/gen/test_write.py
./.venv/bin/pytest tests/test_service.py
```

完整回归：

```bash
./.venv/bin/pytest -q
```
