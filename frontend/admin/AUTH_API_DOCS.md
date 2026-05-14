# 认证 API 文档

本文档描述了 LLM Mental Agent 系统的认证相关 API 接口，包括用户注册、登录、登出等功能。

## 基础信息

- API 基础路径：`/auth`
- 认证方式：Bearer Token（JWT）
- 响应格式：统一的 JSON 格式，包含 code、msg、data 和 rows 字段

## 安全说明

- 密码使用 Argon2 算法加密存储
- JWT Token 有效期为 30 分钟
- 所有密码字段在传输和存储时都会进行加密处理

## 接口列表

### 1. 用户注册

#### 1.1 用户注册

- **接口**：`POST /auth/register`
- **描述**：创建新用户账号
- **请求体**：
  ```json
  {
    "username": "user@example.com",
    "password": "password123",
    "confirmPassword": "password123"
  }
  ```
- **请求参数说明**：
  - `username`：用户邮箱（必填，必须是有效的邮箱格式）
  - `password`：密码（必填，长度不超过72字节）
  - `confirmPassword`：确认密码（必填，必须与password一致）

- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "注册成功"
  }
  ```

- **错误响应**：
  ```json
  {
    "code": 400,
    "msg": "两次输入的密码不一致"
  }
  ```
  ```json
  {
    "code": 400,
    "msg": "用户已存在"
  }
  ```

### 2. 用户登录

#### 2.1 用户登录

- **接口**：`POST /auth/login`
- **描述**：用户登录，获取访问令牌
- **请求体**：
  ```json
  {
    "username": "user@example.com",
    "password": "password123",
    "code": "123456"
  }
  ```
- **请求参数说明**：
  - `username`：用户邮箱（必填）
  - `password`：密码（必填）
  - `code`：邮箱验证码（可选，当前版本暂不使用）

- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "userInfo": {
        "userId": "550e8400-e29b-41d4-a716-446655440000",
        "username": "user@example.com",
        "nickName": "user",
        "avatar": "",
        "roles": ["user"],
        "rolePermission": [],
        "menuPermission": [],
        "tenantId": "default"
      }
    }
  }
  ```

- **错误响应**：
  ```json
  {
    "code": 401,
    "msg": "用户名或密码错误"
  }
  ```

### 3. 邮箱验证码

#### 3.1 发送邮箱验证码

- **接口**：`POST /auth/resource/email/code`
- **描述**：向指定邮箱发送验证码（当前版本为模拟实现）
- **请求体**：
  ```json
  {
    "username": "user@example.com"
  }
  ```
- **请求参数说明**：
  - `username`：用户邮箱（必填）

- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "验证码发送成功"
  }
  ```

- **错误响应**：
  ```json
  {
    "code": 500,
    "msg": "发送验证码失败"
  }
  ```

### 4. 用户信息

#### 4.1 获取当前用户信息

- **接口**：`GET /auth/me`
- **描述**：获取当前登录用户的详细信息
- **请求头**：
  ```
  Authorization: Bearer <token>
  ```
- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": {
      "userInfo": {
        "userId": "550e8400-e29b-41d4-a716-446655440000",
        "username": "user@example.com",
        "nickName": "user",
        "avatar": "",
        "roles": ["user"],
        "rolePermission": [],
        "menuPermission": [],
        "tenantId": "default"
      }
    }
  }
  ```

- **错误响应**：
  ```json
  {
    "code": 401,
    "msg": "未登录"
  }
  ```

### 5. 用户登出

#### 5.1 用户登出

- **接口**：`POST /auth/logout`
- **描述**：用户登出（主要由前端处理，清除本地token）
- **请求头**：
  ```
  Authorization: Bearer <token>
  ```
- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "登出成功"
  }
  ```

### 6. 健康检查

#### 6.1 认证服务健康检查

- **接口**：`GET /auth/`
- **描述**：检查认证服务是否正常运行
- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "认证服务正常运行"
  }
  ```

## 数据模型

### 用户信息模型 (LoginUser)

| 字段 | 类型 | 描述 |
|------|------|------|
| userId | string | 用户唯一标识符 |
| username | string | 用户邮箱 |
| nickName | string | 用户昵称 |
| avatar | string | 用户头像URL |
| roles | array | 用户角色列表 |
| rolePermission | array | 角色权限列表 |
| menuPermission | array | 菜单权限列表 |
| tenantId | string | 租户ID |

### 登录响应模型 (LoginVO)

| 字段 | 类型 | 描述 |
|------|------|------|
| token | string | 访问令牌 |
| access_token | string | 访问令牌（与token相同） |
| userInfo | LoginUser | 用户信息对象 |

## 错误处理

所有接口返回统一的错误格式：

```json
{
  "code": 错误码,
  "msg": "错误信息"
}
```

常见错误码：
- 400：请求参数错误
- 401：未登录或认证失败
- 500：服务器内部错误

## 权限说明

- 注册接口：无需认证
- 登录接口：无需认证
- 邮箱验证码接口：无需认证
- 获取用户信息接口：需要有效的JWT Token
- 登出接口：需要有效的JWT Token

## Token 使用说明

### 获取 Token

通过登录接口获取：

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}' \
  http://localhost:8002/auth/login
```

### 使用 Token

在需要认证的接口请求头中添加：

```
Authorization: Bearer <token>
```

### Token 有效期

- 默认有效期为 30 分钟
- 过期后需要重新登录获取新的 Token

## 示例请求

### 注册新用户

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "username": "newuser@example.com",
    "password": "password123",
    "confirmPassword": "password123"
  }' \
  http://localhost:8002/auth/register
```

### 用户登录

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123"
  }' \
  http://localhost:8002/auth/login
```

### 获取当前用户信息

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8002/auth/me
```

### 用户登出

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8002/auth/logout
```

### 发送邮箱验证码

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com"
  }' \
  http://localhost:8002/auth/resource/email/code
```

## 注意事项

1. **密码安全**：密码在传输和存储时都会进行加密，建议使用强密码
2. **Token 管理**：Token 应该妥善保管，不要在客户端代码中硬编码
3. **邮箱验证**：当前版本的邮箱验证码功能为模拟实现，实际项目中需要集成真实的邮件服务
4. **用户角色**：新注册的用户默认角色为 "user"，管理员权限需要通过后台设置
5. **会话管理**：由于使用 JWT，登出主要由前端处理（清除本地存储的 token）

