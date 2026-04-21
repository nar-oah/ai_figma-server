# figma-to-svelte

FastAPI 服务，输入 Figma 设计稿链接与 Token，调用官方 `GET /v1/files/:key` 和可选的 `GET /v1/files/:key/variables/local`，清洗页面树、组件树、样式与变量绑定，再生成 Svelte + UnoCSS 代码。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 接口

`POST /api/generate`

```json
{
  "url": "https://www.figma.com/design/<file_key>/<file_name>",
  "token": "<figma_token>",
  "out_dir": "generated",
  "use_vars": true
}
```

返回值会给出生成目录、页面路由、组件名和写出的文件列表。

## 生成结果

输出目录默认会生成：

- `uno.config.ts`
- `src/app.css`
- `src/routes/+layout.svelte`
- `src/routes/generated/<page>/+page.svelte`
- `src/lib/generated/components/*.svelte`
- `src/lib/generated/meta.json`
