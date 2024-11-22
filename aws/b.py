from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    print("\n收到GET请求，直接进入主页")
    return RedirectResponse(url="http://localhost:8501")

@app.post("/mp")
async def marketplace(request: Request):
    try:
        data = await request.json()
        print("\n收到POST请求，内容如下：")
        print("-" * 50)
        for key, value in data.items():
            print(f"{key}: {value}")
        print("-" * 50)
        
        if "x-amzn-marketplace-token" in data:
            print("✅ 这是一个 Marketplace 请求")
            redirect_url = "http://localhost:8501"
            print(f"准备重定向到: {redirect_url}")
            return {"redirect": redirect_url}
        else:
            print("��� 这不是一个 Marketplace 请求")
            return {"message": "not a marketplace request"}
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("服务器启动在 http://localhost:80")
    uvicorn.run(app, host="0.0.0.0", port=80) 