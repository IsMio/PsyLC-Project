# 管理员 API 文档

本文档描述了 LLM Mental Agent 系统的管理员 API 接口，用于系统管理和监控。

## 基础信息

- API 基础路径：`/admin`
- 认证方式：Bearer Token（JWT）
- 响应格式：统一的 JSON 格式，包含 code、msg、data 和 rows 字段

## 认证要求

所有管理员 API 接口都需要管理员权限，在请求头中添加：

```
Authorization: Bearer <token>
```

其中 `<token>` 是通过 `/auth/login` 接口获取的访问令牌。

## 接口列表

### 1. 知识库管理

#### 1.1 创建知识库条目

- **接口**：`POST /admin/knowledge-base`
- **描述**：创建新的知识库条目
- **请求体**：
  ```json
  {
    "title": "知识库标题",
    "content": "知识库内容",
    "tags": ["标签1", "标签2"]
  }
  ```
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": {
      "id": "doc_123",
      "title": "知识库标题",
      "content": "知识库内容",
      "tags": ["标签1", "标签2"],
      "created_at": 1620000000
    }
  }
  ```

#### 1.2 获取知识库列表

- **接口**：`GET /admin/knowledge-base/list`
- **描述**：获取知识库条目列表，支持分页和关键词搜索
- **参数**：
  - `pageNum`：页码，默认 1
  - `pageSize`：每页数量，默认 25
  - `keyword`：搜索关键词（可选）
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "rows": [
      {
        "id": "doc_123",
        "title": "知识库标题",
        "content": "知识库内容",
        "tags": ["标签1", "标签2"],
        "created_at": 1620000000
      }
    ]
  }
  ```

#### 1.3 更新知识库条目

- **接口**：`PUT /admin/knowledge-base`
- **描述**：更新知识库条目
- **请求体**：
  ```json
  {
    "id": "doc_123",
    "title": "更新后的标题",
    "content": "更新后的内容",
    "tags": ["更新后的标签"]
  }
  ```
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "更新成功"
  }
  ```

#### 1.4 删除知识库条目

- **接口**：`DELETE /admin/knowledge-base/{ids}`
- **描述**：删除一个或多个知识库条目（逗号分隔多个ID）
- **参数**：
  - `ids`：知识库条目ID，多个ID用逗号分隔
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "删除成功"
  }
  ```

### 2. 用户管理

#### 2.1 获取用户列表

- **接口**：`GET /admin/user/list`
- **描述**：获取用户列表，支持分页和关键词搜索
- **参数**：
  - `pageNum`：页码，默认 1
  - `pageSize`：每页数量，默认 25
  - `keyword`：搜索关键词（可选）
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "rows": [
      {
        "id": "user_123",
        "username": "user@example.com",
        "display_name": "用户名称",
        "roles": ["user"],
        "created_at": 1620000000,
        "avatar": ""
      }
    ]
  }
  ```

#### 2.2 更新用户信息

- **接口**：`PUT /admin/user`
- **描述**：更新用户信息
- **请求体**：
  ```json
  {
    "userId": "user_123",
    "display_name": "新的用户名称",
    "roles": ["user", "admin"],
    "avatar": "https://example.com/avatar.jpg"
  }
  ```
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "更新成功"
  }
  ```

#### 2.3 删除用户

- **接口**：`DELETE /admin/user/{ids}`
- **描述**：删除一个或多个用户（逗号分隔多个ID）
- **参数**：
  - `ids`：用户ID，多个ID用逗号分隔
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "删除成功"
  }
  ```

### 3. 系统状态监控

#### 3.1 获取系统运行状态

- **接口**：`GET /admin/system/status`
- **描述**：获取系统运行状态信息
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": {
      "cpu_usage": 10.5,
      "memory_usage": 65.2,
      "disk_usage": 45.8,
      "uptime": 3600,
      "active_sessions": 10
    }
  }
  ```

### 4. 模型调用统计

#### 4.1 获取模型调用情况统计

- **接口**：`GET /admin/model/usage`
- **描述**：获取模型调用的总体统计信息
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": {
      "total_tokens": 1000000,
      "total_requests": 5000,
      "avg_response_time": 1.5,
      "today_tokens": 100000,
      "today_requests": 500
    }
  }
  ```

#### 4.2 获取模型调用详细统计

- **接口**：`GET /admin/model/usage/detail`
- **描述**：获取模型调用的详细统计，按天统计
- **参数**：
  - `days`：统计天数，默认 7
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": [
      {
        "date": "2026-03-01",
        "tokens": 100000,
        "requests": 500,
        "avg_time": 1.5
      },
      {
        "date": "2026-03-02",
        "tokens": 110000,
        "requests": 550,
        "avg_time": 1.6
      }
    ]
  }
  ```

### 5. 健康检查

#### 5.1 管理员 API 健康检查

- **接口**：`GET /admin/health`
- **描述**：检查管理员 API 是否正常运行
- **响应**：
  ```json
  {
    "code": 200,
    "msg": "管理员API正常运行"
  }
  ```

## 错误处理

所有接口返回统一的错误格式：

```json
{
  "code": 错误码,
  "msg": "错误信息"
}
```

常见错误码：
- 401：未登录
- 403：无管理员权限
- 400：请求参数错误
- 500：服务器内部错误

## 权限说明

所有管理员接口都需要用户拥有 `admin` 角色，否则会返回 403 错误。

## 示例请求

使用 curl 发送请求的示例：

```bash
# 获取系统状态
curl -H "Authorization: Bearer <token>" http://localhost:8002/admin/system/status

# 获取用户列表
curl -H "Authorization: Bearer <token>" "http://localhost:8002/admin/user/list?pageNum=1&pageSize=25"

# 创建知识库条目
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"title": "测试知识库", "content": "测试内容"}' http://localhost:8002/admin/knowledge-base
```

