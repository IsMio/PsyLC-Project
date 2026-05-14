# PsyLC Project

PsyLC Project 是一个面向校园心理支持场景的后端原型系统。项目基于 FastAPI、LangChain、Chroma、SQLite 和 Redis 相关能力，提供用户认证、会话管理、RAG 知识库检索增强、情感识别、内容过滤和后台管理接口。

本项目用于原型验证和毕业设计实验，不可替代专业心理咨询、医学诊断或紧急危机干预服务。

## 功能概览

- 用户认证：支持注册、登录、登出、令牌校验和管理员权限控制。
- 会话管理：支持会话创建、查询、更新、删除和历史消息持久化。
- 对话生成：通过 LangChain 编排提示词、历史消息、RAG 上下文和大模型调用。
- RAG 检索增强：使用 Chroma 向量库检索心理健康知识片段，辅助生成回复。
- 情感识别：识别用户输入的情绪极性、强度和情绪标签，并生成回复策略提示。
- 内容过滤：对诊断化、用药、自伤、暴力、仇恨和绝对化表达进行规则过滤与复核。
- 知识库管理：支持文本、文件和数据集导入，后台异步切分、入库和索引。
- 系统管理：提供配置、指标、用户、知识文档和输出过滤策略相关管理接口。

## 技术栈

- Python 3.12
- FastAPI
- LangChain
- Chroma
- SQLite
- Redis
- DashScope/OpenAI-compatible API
- Docker

## 目录结构

```text
.
├── api/                 # FastAPI 路由层
│   └── v1/              # auth、chat、admin 等接口
├── core/                # 核心业务模块
│   ├── admin/           # 管理后台服务
│   ├── chat/            # 对话、情感识别、消息历史
│   ├── filter/          # 内容过滤和输出策略
│   ├── knowledge/       # 知识库、文档解析和入库队列
│   └── utils/           # 数据集导入、Prompt 优化工具
├── frontend/            # 前端项目
│   ├── admin/           # 管理端，Vue 3 + Ant Design Vue
│   └── guest/           # 用户聊天端，Vue 3 + Element Plus
├── data/                # SQLite、Chroma、配置和测试数据
├── docs/                # 设计文档和计划文档
├── scripts/             # 辅助脚本
├── tests/               # 单元测试和专项测试
├── main.py              # FastAPI 应用入口
├── config.py            # 配置加载
├── prompt.txt           # 对话 Prompt 模板
├── Dockerfile
└── docker-compose.yml
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. 安装依赖

项目的 `requirements.txt` 当前按 UTF-16 编码保存。Windows 环境通常可以直接安装：

```bash
pip install -r requirements.txt
```

如果环境读取异常，可先转换为 UTF-8：

```bash
python -c "from pathlib import Path; Path('requirements-utf8.txt').write_text(Path('requirements.txt').read_text(encoding='utf-16'), encoding='utf-8')"
pip install -r requirements-utf8.txt
```

### 3. 配置密钥

配置文件位于：

```text
data/config.yaml
```

建议通过环境变量覆盖真实密钥，避免将 API Key 提交到仓库：

```powershell
$env:DASHSCOPE_API_KEY="your_api_key"
$env:ASSIST_API_KEY="your_assist_api_key"
```

Linux/macOS:

```bash
export DASHSCOPE_API_KEY="your_api_key"
export ASSIST_API_KEY="your_assist_api_key"
```

常用配置项：

- `dashscope.api_base_url`：主模型接口地址。
- `dashscope.assist_api_base_url`：辅助模型接口地址。
- `dashscope.model_name`：对话模型名称。
- `dashscope.embeddings_model_name`：向量模型名称。
- `app.chroma_persist_dir`：Chroma 持久化目录。
- `app.chroma_collection_name`：Chroma 集合名称。
- `app.output_filter_enabled`：是否启用内容过滤。
- `db.path`：SQLite 数据库路径。

### 4. 初始化管理员账号

```bash
python init_admin.py --username admin --password admin123 --display-name 系统管理员
```

### 5. 启动服务

开发模式：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

普通模式：

```bash
python main.py
```

服务启动后可访问：

```text
http://localhost:8002/
```

## 前端启动

前端代码位于 `frontend/`，当前包含两个独立 Vite 应用：

- `frontend/guest`：用户聊天端。
- `frontend/admin`：管理后台。

两个前端都使用 pnpm。首次运行前请先安装 Node.js 20+，并启用 Corepack：

```bash
corepack enable
```

### 启动用户聊天端

```bash
cd frontend/guest
pnpm install
pnpm dev
```

开发环境下，聊天端通过 Vite 代理访问后端：

```text
/dev-api -> http://localhost:8002
```

如果不使用 mock，请确认 `frontend/guest/.env.development` 中：

```text
VITE_USE_MOCK = 'false'
VITE_API_URL = '/dev-api'
```

### 启动管理后台

```bash
cd frontend/admin
pnpm install
pnpm dev
```

管理端开发环境默认代理到：

```text
http://localhost:8002
```

如需修改后端地址，可在 `frontend/admin/.env` 中配置：

```text
VITE_API_TARGET=http://localhost:8002
```

### 前端生产构建

用户聊天端：

```bash
cd frontend/guest
pnpm build
```

管理后台：

```bash
cd frontend/admin
pnpm build
```

构建产物默认输出到各自目录下的 `dist/`。

## Docker 部署

当前 `docker-compose.yml` 会同时启动三个服务：

- `backend`：后端 API，端口 `8002`。
- `frontend-guest`：用户聊天端，端口 `8080`。
- `frontend-admin`：管理后台，端口 `8081`。

### 仅构建后端镜像

```bash
docker build -t psylc-backend:latest .
```

### 仅启动后端容器

```bash
docker run -d ^
  --name psylc-backend ^
  -p 8002:8002 ^
  -v %cd%/data:/app/data ^
  -v %cd%/prompt.txt:/app/prompt.txt ^
  -e DASHSCOPE_API_KEY=your_api_key ^
  -e ASSIST_API_KEY=your_assist_api_key ^
  psylc-backend:latest
```

Linux/macOS:

```bash
docker run -d \
  --name psylc-backend \
  -p 8002:8002 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/prompt.txt:/app/prompt.txt" \
  -e DASHSCOPE_API_KEY=your_api_key \
  -e ASSIST_API_KEY=your_assist_api_key \
  psylc-backend:latest
```

### 使用 Docker Compose 启动全套服务

```bash
docker compose up -d --build
```

默认端口映射：

```text
后端 API:    http://localhost:8002
用户聊天端:  http://localhost:8080
管理后台:    http://localhost:8081
```

Docker 模式下，前端容器通过 Nginx 反向代理访问后端容器：

- 用户聊天端：`/prod-api/* -> backend:8002/*`
- 管理后台：`/auth/* -> backend:8002/auth/*`
- 管理后台：`/admin/* -> backend:8002/admin/*`

如需单独构建前端镜像：

```bash
docker build -t psylc-frontend-guest:latest frontend/guest
docker build -t psylc-frontend-admin:latest frontend/admin
```

## 核心流程

### 对话生成流程

1. 前端调用 `/chat/send` 发送用户消息。
2. 系统校验会话和用户信息。
3. 情感识别模块分析用户情绪并生成回复策略。
4. RAG 模块从 Chroma 检索相关知识片段。
5. LangChain 将历史消息、检索结果和策略提示组合为 Prompt。
6. 大模型生成回复，支持流式和非流式返回。
7. ContentFilter 对回复进行安全过滤。
8. 系统保存用户消息和助手回复。

### 知识库入库流程

1. 管理端上传文本、文件或数据集。
2. `KnowledgeService` 解析文档内容。
3. 使用 `RecursiveCharacterTextSplitter` 切分文本。
4. 默认切片大小为 600 字符，重叠 120 字符。
5. 调用嵌入模型生成向量。
6. 向量写入 Chroma，元信息写入 SQLite。
7. 后续对话通过语义相似度检索知识片段。

### 内容过滤流程

1. 对模型回复执行自定义规则匹配。
2. 未命中时执行内置风险规则匹配。
3. 可选调用 LLM 审查器进行语义复核。
4. 命中风险时返回替代安全话术。
5. 流式响应场景下通过 `replace` 信号替换原输出。

## 主要接口

认证相关：

- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/resource/email/code`

聊天相关：

- `POST /chat/send`
- `GET /system/session/list`
- `POST /system/session`
- `PUT /system/session`
- `DELETE /system/session/{ids}`
- `GET /system/message/list`

管理相关：

- `GET /admin/health`
- `GET /admin/system/status`
- `GET /admin/model/usage`
- `GET /admin/model/usage/detail`
- `GET /admin/system/config`
- `PUT /admin/system/config`
- `GET /admin/output-filter/policy`
- `PUT /admin/output-filter/policy`
- `GET /admin/user/list`
- `PUT /admin/user`
- `DELETE /admin/user/{ids}`
- `GET /admin/knowledge-base/list`
- `POST /admin/knowledge-base/text`
- `POST /admin/knowledge-base/file`
- `POST /admin/knowledge-base/dataset`
- `GET /admin/knowledge-base/batches`
- `GET /admin/knowledge-base/jobs`

实际接口以 `api/v1/*.py` 中路由定义为准。

