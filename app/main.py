from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import chat
from app.api.v1 import documents
from app.core.langsmith_init import init_langsmith

# 启动 LangSmith 追踪
init_langsmith()
print("222")

app = FastAPI(title="RAG Agent Backend", version="1.0.0")

# 跨域配置（允许前端 localhost:5173 访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(documents.router)

@app.get("/")
async def root():
    return {"message": "RAG Agent API is running", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)