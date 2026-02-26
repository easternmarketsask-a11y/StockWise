from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from api_handler import CloverAPIHandler
from data_engine import DataEngine
from ui_render import UIRenderer
from chart_engine import ChartEngine
from inventory_alert import InventoryAlert
from trend_analysis import TrendAnalysis
from multi_lang import MultiLanguage
from product_ai_manager import ProductAIManager
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
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# 初始化组件
api_handler = CloverAPIHandler()
data_engine = DataEngine()
ui_renderer = UIRenderer()
chart_engine = ChartEngine()
inventory_alert = InventoryAlert(api_handler)
trend_analyzer = TrendAnalysis(api_handler)
ai_manager = ProductAIManager(api_handler)
multi_lang = MultiLanguage()

@app.get("/", response_class=HTMLResponse)
async def root():
    """提供主页面"""
    # 这里可以返回一个简单的 HTML 页面或重定向到 Streamlit
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StockWise - Eastern Market</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .logo { max-width: 200px; margin-bottom: 20px; }
            .status { color: #2E7D32; font-size: 18px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <img src="/assets/eastern_market_logo.jpeg" alt="Eastern Market Logo" class="logo" onerror="this.style.display='none'">
        <h1>StockWise - Eastern Market</h1>
        <div class="status">✅ API 服务正在运行</div>
        <p><a href="/docs">查看 API 文档</a></p>
        <p><a href="/health">健康检查</a></p>
        <p><a href="/api/products">获取商品数据</a></p>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "StockWise API", "version": "1.0.0"}

@app.get("/api/products")
async def get_products():
    """获取商品数据"""
    try:
        inventory = api_handler.fetch_full_inventory()
        if inventory is None:
            raise HTTPException(status_code=500, detail="商品数据加载失败")
        return {"products": inventory, "count": len(inventory)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales/{product_id}")
async def get_product_sales(product_id: str, start_date: str = None, end_date: str = None):
    """获取特定商品的销售数据"""
    try:
        # 这里可以添加日期处理逻辑
        sales_data = api_handler.fetch_targeted_sales([product_id], 0, 9999999999999)
        return {"product_id": product_id, "sales": sales_data}
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
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
