from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import requests
import pandas as pd
from datetime import datetime
import uvicorn

app = FastAPI(title="StockWise API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
try:
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
except RuntimeError:
    pass  # 如果 assets 目录不存在

@app.get("/", response_class=HTMLResponse)
async def root():
    """提供主页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StockWise - Eastern Market</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .logo { max-width: 200px; margin-bottom: 20px; }
            .status { color: #2E7D32; font-size: 18px; margin: 20px 0; }
            .api-list { text-align: left; max-width: 600px; margin: 0 auto; }
            .api-item { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🛒 StockWise - Eastern Market</h1>
        <div class="status">✅ API 服务正在运行</div>
        <p>版本: 1.0.0 | 部署时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        
        <div class="api-list">
            <h3>📡 可用 API 端点:</h3>
            <div class="api-item">
                <strong>GET /health</strong> - 健康检查
            </div>
            <div class="api-item">
                <strong>GET /api/products</strong> - 获取商品数据
            </div>
            <div class="api-item">
                <strong>GET /api/store/carousel-banners</strong> - 轮播图数据
            </div>
            <div class="api-item">
                <strong>GET /docs</strong> - API 文档 (Swagger)
            </div>
        </div>
        
        <p><img src="/assets/eastern_market_logo.jpeg" alt="Eastern Market Logo" style="max-width: 200px;" onerror="this.style.display='none'"></p>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy", 
        "service": "StockWise API", 
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "production")
    }

@app.get("/api/products")
async def get_products():
    """获取商品数据"""
    try:
        # 模拟数据，实际应该调用 Clover API
        mock_products = [
            {
                "id": "TEST001",
                "name": "测试商品 1",
                "sku": "SKU001",
                "price": 10.99,
                "stock": 100
            },
            {
                "id": "TEST002", 
                "name": "测试商品 2",
                "sku": "SKU002",
                "price": 15.99,
                "stock": 50
            }
        ]
        
        return {"products": mock_products, "count": len(mock_products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/store/carousel-banners")
async def get_carousel_banners():
    """获取轮播图数据"""
    return {
        "banners": [
            {
                "id": 1,
                "title": "欢迎来到 Eastern Market",
                "image": "/assets/eastern_market_logo.jpeg",
                "link": "/"
            },
            {
                "id": 2,
                "title": "优质商品",
                "image": "/assets/eastern_market_logo.jpeg", 
                "link": "/api/products"
            }
        ]
    }

@app.get("/api/test/clover")
async def test_clover_api():
    """测试 Clover API 连接"""
    try:
        # 这里可以添加实际的 Clover API 测试
        return {
            "status": "Clover API 测试端点",
            "message": "需要配置正确的 API Keys",
            "clover_merchant_id": os.environ.get("CLOVER_MERCHANT_ID", "未配置"),
            "has_api_key": bool(os.environ.get("CLOVER_API_KEY"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
