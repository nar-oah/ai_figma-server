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

## 服务器部署

以下步骤按仓库内的 `deploy/figma-doc.service` 约定部署，默认项目目录为 `/home/admin/figma`，运行用户为 `admin`，服务端口为 `8000`。如果服务器路径或用户不同，需要同步修改 service 文件中的 `User`、`Group`、`WorkingDirectory`、`EnvironmentFile` 和 `ExecStart`。

### 1. 准备运行环境

服务器需要 Python 3.12+ 和 PostgreSQL。将代码放到 `/home/admin/figma` 后安装依赖：

```bash
cd /home/admin/figma
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 初始化数据库

创建 `figma` 数据库后执行建表脚本：

```bash
sudo -u postgres createdb figma
sudo -u postgres psql -d figma -f /home/admin/figma/deploy/schema.sql
```

如果使用独立数据库账号，需要先创建账号并授予 `figma` 数据库权限，再在 `.env` 中写入对应连接信息。

### 3. 配置环境变量

在 `/home/admin/figma/.env` 写入：

```bash
FIGMA_TOKEN=<figma_token>
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=figma
PGUSER=<db_user>
PGPASSWORD=<db_password>
```

`psycopg.connect()` 会自动读取 `PGHOST`、`PGPORT`、`PGDATABASE`、`PGUSER`、`PGPASSWORD` 等环境变量。不要把 `.env` 提交到代码仓库。

### 4. 安装 systemd 服务

```bash
sudo cp /home/admin/figma/deploy/figma-doc.service /etc/systemd/system/figma-doc.service
sudo systemctl daemon-reload
sudo systemctl enable --now figma-doc
sudo systemctl status figma-doc
```

查看服务日志：

```bash
journalctl -u figma-doc -f
```

服务默认通过 `0.0.0.0:8000` 对外监听。生产环境建议只在内网或反向代理后开放端口；如果只允许本机 Nginx 代理访问，可以把 `deploy/figma-doc.service` 里的 `--host 0.0.0.0` 改为 `--host 127.0.0.1`。

### 5. 部署后自检

```bash
curl -X POST "http://<server_host>:8000/api/doc?url=https://www.figma.com/design/<file_key>/<file_name>" \
  -F "file=@tokens.json"
```

成功时接口返回生成的定位 token。

## 接口

### `POST /api/doc`

请求参数：

- `url`：Figma 文件链接，放在 query string 中。
- `file`：Figma 导出的类似 `tokens.json` 的 JSON 文件，使用 multipart form 上传。

示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/doc?url=https://www.figma.com/design/<file_key>/<file_name>" \
  -F "file=@tokens.json"
```

响应只返回生成的定位 token。数据库连接使用 `psycopg.connect()` 无参数读取 `PGHOST`、`PGPORT`、`PGDATABASE`、`PGUSER`、`PGPASSWORD` 等环境变量。

建表 SQL 位于 `deploy/schema.sql`，需要在 `figma` 数据库中先执行。

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
├── deploy/
│   ├── figma-doc.service
│   └── schema.sql
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
