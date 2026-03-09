import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.auth import router as auth_router, verify_token
from api.chat import router as chat_router
from core.chat_process import ChatProcess

# 初始化FastAPI应用
app = FastAPI(lifespan=ChatProcess.lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 需要验证token的路径
PROTECTED_PATHS = [
    "/system/session/list",
    "/system/message/list"
]

# 验证token的中间件
@app.middleware("http")
async def verify_token_middleware(request: Request, call_next):
    # 跳过OPTIONS请求的token验证
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    # 检查请求路径是否在保护列表中
    path = request.url.path
    for protected_path in PROTECTED_PATHS:
        if path.startswith(protected_path):
            # 获取Authorization头
            authorization = request.headers.get("Authorization")
            if not authorization:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "未提供Authorization头"}
                )
            
            # 提取token
            token = authorization.replace("Bearer ", "")
            
            # 验证token
            payload = verify_token(token)
            if not payload:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "无效的token"}
                )
            print(f"Token验证成功，用户信息：{payload}")
            # 将用户信息添加到请求中
            request.state.user = payload
            break
    
    # 继续处理请求
    response = await call_next(request)
    return response
# 注册路由
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "LLM Mental Agent API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")