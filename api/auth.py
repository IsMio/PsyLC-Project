import asyncio
import uuid
import time
import json
import random
import string
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import sqlite3
from passlib.context import CryptContext
from config import Config
# 初始化APIRouter
router = APIRouter(prefix="/auth", tags=["auth"])


# 使用内存字典来管理token
# 尝试导入redis
redis_client = None
token_store = {}
try:
    import redis
    try:
        redis_client = redis.Redis(
            host="localhost",
            port=6379,
            db=0
        )
        # 测试连接
        redis_client.ping()
        print("Redis连接成功")
    except Exception as e:
        print(f"Redis连接失败: {str(e)}")
        # 如果Redis连接失败，使用内存字典作为备用
        redis_client = None
        token_store = {}
except ImportError:
    print("Redis库未安装，使用内存字典作为备用")
    redis_client = None
    token_store = {}



# 初始化SQLite连接
def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 创建users表
def create_users_table():
    """创建users表"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS "users"
                   (
                       "id"             TEXT,
                       "display_name"   TEXT,
                       "created_at"     INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                       "username"       TEXT,
                       "roles"          TEXT,
                       "password_hash"  TEXT,
                       "avatar"         TEXT,
                       "rolePermission" TEXT,
                       "menuPermission" TEXT,
                       "tenantId"       text,
                       PRIMARY KEY ("id")
                   )
                   ''')
    conn.commit()
    conn.close()


# 初始化表结构
create_users_table()

# 密码加密上下文
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Token配置
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# 统一响应结构
class BaseResponse(BaseModel):
    code: int = 200
    msg: str = "ok"
    data: Optional[Dict[str, Any]] = None
    rows: Optional[list] = None


# 登录请求模型
class LoginDTO(BaseModel):
    username: str
    password: str
    code: Optional[str] = None
    confirmPassword: Optional[str] = None


# 注册请求模型
class RegisterDTO(BaseModel):
    username: str
    password: str
    confirmPassword: Optional[str] = None


# 邮箱验证码请求模型（保留但暂时不使用）
class EmailCodeDTO(BaseModel):
    username: str


# 用户信息模型
class LoginUser(BaseModel):
    userId: str
    username: str
    nickName: str
    avatar: str
    roles: list
    rolePermission: list
    menuPermission: list
    tenantId: str


# 登录响应模型
class LoginVO(BaseModel):
    token: Optional[str] = None
    access_token: Optional[str] = None
    userInfo: Optional[LoginUser] = None


# 工具函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 限制密码长度为72字节，bcrypt的最大限制
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    # 限制密码长度为72字节，bcrypt的最大限制
    return pwd_context.hash(password[:72])


def generate_random_token(length: int = 32) -> str:
    """生成随机token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = time.time() + expires_delta * 60
    else:
        expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode.update({"exp": expire})
    
    # 生成随机token
    token = generate_random_token()
    
    # 将token存储到Redis
    if redis_client:
        try:
            redis_client.setex(
                f"token:{token}",
                int(expire - time.time()),
                json.dumps(to_encode)
            )
        except Exception as e:
            print(f"Redis存储token失败: {str(e)}")
    else:
        # 使用内存字典作为备用
        token_store[token] = {
            "payload": to_encode,
            "exp": expire
        }
    
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """验证令牌"""
    try:
        # 首先检查token是否在Redis中
        if redis_client:
            try:
                payload_str = redis_client.get(f"token:{token}")
                if not payload_str:
                    return None
                payload = json.loads(payload_str)
                # 检查token是否过期
                if payload.get("exp") < time.time():
                    # 删除过期token
                    redis_client.delete(f"token:{token}")
                    return None
                return payload
            except Exception as e:
                print(f"Redis验证token失败: {str(e)}")
        else:
            # 使用内存字典作为备用
            if token not in token_store:
                return None
            token_data = token_store[token]
            # 检查token是否过期
            if token_data["exp"] < time.time():
                # 删除过期token
                del token_store[token]
                return None
            return token_data["payload"]
        
        return None
    except Exception as e:
        print(f"验证token失败: {str(e)}")
        return None


def generate_verification_code() -> str:
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=6))


async def send_email_verification_code(email: str, code: str) -> bool:
    """发送邮箱验证码（模拟）"""
    # 实际项目中这里应该调用邮件服务
    print(f"向 {email} 发送验证码: {code}")
    return True


# 依赖项
async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """获取当前用户"""
    if not authorization:
        return None

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        return None

    # 从SQLite中获取用户信息
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (payload.get('sub'),))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        return None

    # 转换为字典
    user_data = {
        "userId": user_row["id"],
        "username": user_row["username"],
        "nickName": user_row["display_name"],
        "avatar": user_row["avatar"],
        "roles": json.loads(user_row["roles"]) if user_row["roles"] else [],
        "rolePermission": json.loads(user_row["rolePermission"]) if user_row["rolePermission"] else [],
        "menuPermission": json.loads(user_row["menuPermission"]) if user_row["menuPermission"] else [],
        "tenantId": user_row["tenantId"],
        "created_at": user_row["created_at"]
    }

    return user_data


# 接口实现
@router.post("/login", response_model=BaseResponse)
async def login(req: LoginDTO):
    """登录接口"""
    try:
        # 从SQLite中获取用户信息
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
        user_row = cursor.fetchone()
        conn.close()

        if not user_row:
            return BaseResponse(code=402, msg="用户名或密码错误")

        # 验证密码
        if not verify_password(req.password, user_row["password_hash"]):
            return BaseResponse(code=402, msg="用户名或密码错误")

        # 创建访问令牌
        access_token = create_access_token(data={"sub": req.username, "userId": user_row["id"]})

        # 构建用户信息
        user_info = LoginUser(
            userId=user_row["id"],
            username=user_row["username"],
            nickName=user_row["display_name"],
            avatar=user_row["avatar"],
            roles=json.loads(user_row["roles"]) if user_row["roles"] else [],
            rolePermission=json.loads(user_row["rolePermission"]) if user_row["rolePermission"] else [],
            menuPermission=json.loads(user_row["menuPermission"]) if user_row["menuPermission"] else [],
            tenantId=user_row["tenantId"]
        )

        # 构建登录响应
        login_vo = LoginVO(
            token=access_token,
            access_token=access_token,
            userInfo=user_info
        )

        return BaseResponse(data=login_vo.model_dump())

    except Exception as e:
        return BaseResponse(code=500, msg=f"登录失败: {str(e)}")


@router.post("/register", response_model=BaseResponse)
async def register(req: RegisterDTO):
    """注册接口"""
    try:
        # 限制密码长度为72字节，bcrypt的最大限制
        truncated_password = req.password[:72]

        # 检查用户是否已存在
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return BaseResponse(code=400, msg="用户已存在")

        # 创建新用户
        user_id = str(uuid.uuid4())
        display_name = req.username.split("@")[0]
        password_hash = get_password_hash(truncated_password)
        roles = json.dumps(["user"])
        role_permission = json.dumps([])
        menu_permission = json.dumps([])
        tenant_id = "default"
        created_at = int(time.time())
        print(get_password_hash(truncated_password))
        # 保存用户信息到SQLite
        cursor.execute('''
                       INSERT INTO users (id, display_name, created_at, username, roles, password_hash, avatar,
                                          rolePermission, menuPermission, tenantId)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (user_id, display_name, created_at, req.username, roles, password_hash, "", role_permission,
                             menu_permission, tenant_id))
        conn.commit()
        conn.close()

        return BaseResponse(msg="注册成功")

    except Exception as e:
        return BaseResponse(code=500, msg=f"注册失败: {str(e)}")


@router.post("/resource/email/code", response_model=BaseResponse)
async def email_code(req: EmailCodeDTO):
    """发送邮箱验证码（暂时去除验证逻辑）"""
    try:
        # 由于暂时去除了邮件验证部分，直接返回成功消息
        # 实际项目中，这里应该调用邮件服务发送验证码
        print(f"向 {req.username} 发送验证码（模拟）")
        return BaseResponse(msg="验证码发送成功")

    except Exception as e:
        return BaseResponse(code=500, msg=f"发送验证码失败: {str(e)}")


@router.get("/me", response_model=BaseResponse)
async def get_current_user_info(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取当前用户信息"""
    if not current_user:
        return BaseResponse(code=401, msg="未登录")

    # 构建用户信息
    user_info = LoginUser(
        userId=current_user.get("userId"),
        username=current_user.get("username"),
        nickName=current_user.get("nickName"),
        avatar=current_user.get("avatar"),
        roles=current_user.get("roles", []),
        rolePermission=current_user.get("rolePermission", []),
        menuPermission=current_user.get("menuPermission", []),
        tenantId=current_user.get("tenantId")
    )

    return BaseResponse(data={"userInfo": user_info.model_dump()})


@router.post("/logout", response_model=BaseResponse)
async def logout(authorization: Optional[str] = Header(None)):
    """登出接口"""
    if not authorization:
        return BaseResponse(code=401, msg="未提供Authorization头")
    
    # 提取token
    token = authorization.replace("Bearer ", "")
    
    # 从Redis中删除token
    if redis_client:
        try:
            redis_client.delete(f"token:{token}")
        except Exception as e:
            print(f"Redis删除token失败: {str(e)}")
    else:
        # 使用内存字典作为备用
        if token in token_store:
            del token_store[token]
    
    return BaseResponse(msg="登出成功")


@router.get("/")
async def auth_root():
    """认证服务根路径"""
    return BaseResponse(msg="认证服务正常运行")
