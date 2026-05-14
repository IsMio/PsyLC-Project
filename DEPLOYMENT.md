# PsyLC Deployment Guide

本文档说明当前项目的部署方式，包括：

- 后端 FastAPI 服务部署
- 管理后台 `D:\PsyLc_admin` 构建与部署
- 聊天前端 `D:\ruoyi-element-ai` 构建与部署
- Docker 部署
- 环境变量与配置管理

---

## 1. 项目组成

当前实际包含三部分：

1. **后端 API**
   - 路径：`C:\Users\Mio\PycharmProjects\PsyLC-Project`
   - 启动入口：`main.py`
   - 技术栈：FastAPI + SQLite + Chroma + Redis(可选)

2. **管理员后台**
   - 路径：`D:\PsyLc_admin`
   - 技术栈：Vue 3 + Ant Design Vue + Vite

3. **聊天前端**
   - 路径：`D:\ruoyi-element-ai`
   - 技术栈：Vue 3 + Element Plus + Vite

---

## 2. 后端部署

### 2.1 本地直接部署

推荐 Python 版本：`3.12`

#### 安装依赖

注意：项目 `requirements.txt` 当前是 `UTF-16` 编码。

可以直接在 Windows 命令行安装：

```bash
pip install -r requirements.txt
```

如果某些环境读取异常，可先转成 UTF-8：

```bash
python -c "from pathlib import Path; Path('requirements-utf8.txt').write_text(Path('requirements.txt').read_text(encoding='utf-16'), encoding='utf-8')"
pip install -r requirements-utf8.txt
```

#### 启动服务

```bash
python main.py
```

默认监听：

- `0.0.0.0:8002`

#### 初始化管理员账号

```bash
python init_admin.py --username admin --password admin123 --display-name 系统管理员
```

---

### 2.2 生产建议

当前后端是命令行直接跑 `main.py`，适合：

- 本地开发
- 单机部署
- 小规模内网环境

生产环境建议至少做到：

- 使用独立 Python 虚拟环境
- 将 `data/` 挂载到持久化目录
- 配置 Redis
- 使用反向代理（Nginx / Caddy）转发到 `8002`
- 不要把真实 API Key 直接写死在 `data/config.yaml`

---

## 3. Docker 部署

项目根目录已补充：

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`

### 3.1 构建镜像

```bash
docker build -t psylc-backend:latest .
```

### 3.2 启动容器

```bash
docker run -d \
  --name psylc-backend \
  -p 8002:8002 \
  -v ${PWD}/data:/app/data \
  -e DASHSCOPE_API_KEY=your_key \
  psylc-backend:latest
```

### 3.3 使用 docker compose

```bash
docker compose up -d --build
```

默认映射：

- 宿主机 `8002` -> 容器 `8002`

注意事项：

- `data/` 已挂载为持久化目录
- `prompt.txt` 也挂载进容器
- 如果使用 Chroma 和 SQLite，必须保留 `data/` 的持久化

---

## 4. 管理后台部署（D:\PsyLc_admin）

### 4.1 开发启动

```bash
cd D:\PsyLc_admin
pnpm install
pnpm dev
```

本地开发时通过 `vite.config.ts` 代理：

- `/auth` -> `VITE_API_TARGET`
- `/admin` -> `VITE_API_TARGET`

默认后端地址：

- `http://localhost:8002`

### 4.2 生产构建

```bash
cd D:\PsyLc_admin
pnpm install
pnpm build
```

构建产物目录：

- `D:\PsyLc_admin\dist`

### 4.3 部署方式

可部署到任意静态站点服务器：

- Nginx
- Caddy
- OSS / CDN
- 静态文件托管平台

Nginx 示例：

```nginx
server {
    listen 80;
    server_name admin.example.com;

    root /var/www/psylc-admin/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /auth/ {
        proxy_pass http://127.0.0.1:8002;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8002;
    }
}
```

---

## 5. 聊天前端部署（D:\ruoyi-element-ai）

### 5.1 开发启动

```bash
cd D:\ruoyi-element-ai
pnpm install
pnpm dev
```

聊天前端会请求后端接口，例如：

- `/chat/send`
- `/system/message`
- `/system/message/list`

请确保前端运行环境中这些接口被正确代理到后端。

### 5.2 生产构建

```bash
cd D:\ruoyi-element-ai
pnpm install
pnpm build
```

构建产物目录通常为：

- `D:\ruoyi-element-ai\dist`

### 5.3 生产部署

同样可部署到 Nginx 等静态资源服务器。

示例：

```nginx
server {
    listen 80;
    server_name chat.example.com;

    root /var/www/ruoyi-element-ai/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /chat/ {
        proxy_pass http://127.0.0.1:8002;
    }

    location /system/ {
        proxy_pass http://127.0.0.1:8002;
    }

    location /auth/ {
        proxy_pass http://127.0.0.1:8002;
    }
}
```

---

## 6. 环境变量与配置管理

### 6.1 当前配置来源

当前后端配置主要来自两个地方：

1. `data/config.yaml`
2. 环境变量（会覆盖部分字段）

配置读取逻辑见：

- `config.py`

### 6.2 当前已支持的环境变量

后端代码中实际读取了这些环境变量：

- `DASHSCOPE_API_KEY`
- `ALIYUN_API_KEY`
- `DASHSCOPE_API_BASE_URL`
- `ALIYUN_API_BASE_URL`
- `ASSIST_API_KEY`

含义：

- 优先使用环境变量
- 如果环境变量不存在，再回退到 `data/config.yaml`

### 6.3 推荐配置策略

#### 建议放进环境变量的内容

- `DASHSCOPE_API_KEY`
- `ASSIST_API_KEY`
- 其他密钥、令牌、私密地址

#### 建议保留在 `config.yaml` 的内容

- 模型名称
- temperature / top_p
- Chroma 存储路径
- 聊天历史限制
- 输出过滤开关
- 业务提示词

### 6.4 推荐新增 `.env`

建议项目根目录新增 `.env`：

```env
DASHSCOPE_API_KEY=your_real_key
ASSIST_API_KEY=your_real_assist_key
DASHSCOPE_API_BASE_URL=https://api.kittyinfra.net/v1
```

因为 `config.py` 已调用：

```python
load_dotenv()
```

所以 `.env` 会自动生效。

### 6.5 后台配置管理说明

管理员后台已经支持维护白名单配置项：

- 系统配置页面只允许修改白名单字段
- 保存后可点击“确认后重启系统”

说明：

- 白名单配置会写回 `data/config.yaml`
- 敏感字段不会在该页面暴露
- 某些静态配置要重启后端才能完全生效

---

## 7. 数据目录说明

后端依赖以下持久化目录/文件：

- `data/chat_history.db`：SQLite 聊天数据库
- `data/chroma_db/`：Chroma 向量库
- `data/config.yaml`：业务配置文件

部署时必须持久化：

- `data/`

否则会丢失：

- 用户与聊天记录
- 知识库向量数据
- 管理员修改过的配置

---

## 8. 部署顺序建议

推荐顺序：

1. 准备后端环境与 `data/` 持久化目录
2. 配置 `.env` 或宿主机环境变量
3. 启动后端 `python main.py`
4. 执行 `python init_admin.py` 初始化管理员
5. 构建并部署 `D:\PsyLc_admin`
6. 构建并部署 `D:\ruoyi-element-ai`
7. 配置 Nginx / 反向代理
8. 登录管理后台检查系统状态、模型统计、知识库页面

---

## 9. 已知注意事项

- `requirements.txt` 当前是 `UTF-16` 编码，Dockerfile 已做转换处理。
- 后端重启逻辑适用于“命令行直接运行 `python main.py`”的场景。
- 如果以后切到 `uvicorn main:app`、Windows 服务、Docker 编排或 systemd，重启逻辑需要改造。
- 当前 `config.yaml` 中仍存在明文敏感字段示例，生产环境务必改为环境变量。
