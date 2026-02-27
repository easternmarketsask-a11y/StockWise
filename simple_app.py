from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import uvicorn
from typing import List, Dict, Optional

# 导入核心功能模块
from api_handler import CloverAPIHandler
from data_engine import DataEngine
from chart_engine import ChartEngine
from inventory_alert import InventoryAlert
from trend_analysis import TrendAnalysis
from multi_lang import MultiLanguage
from product_ai_manager import ProductAIManager

app = FastAPI(title="StockWise API", version="2.0.0")

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

# 初始化核心模块
api_handler = None
data_engine = DataEngine()
chart_engine = ChartEngine()
ml = MultiLanguage()

def get_api_handler():
    """延迟初始化API处理器"""
    global api_handler
    if api_handler is None:
        api_handler = CloverAPIHandler()
    return api_handler

@app.get("/", response_class=HTMLResponse)
async def root():
    """提供主页面"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StockWise - Eastern Market API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .logo { max-width: 200px; margin-bottom: 20px; }
            .status { color: #2E7D32; font-size: 18px; margin: 20px 0; }
            .api-list { text-align: left; max-width: 800px; margin: 0 auto; }
            .api-item { margin: 10px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            .method { color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
            .get { background: #61affe; }
            .post { background: #49cc90; }
        </style>
    </head>
    <body>
        <h1>🛒 StockWise - Eastern Market API</h1>
        <div class="status">✅ API 服务正在运行</div>
        <p>版本: 2.0.0 | 部署时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        
        <div class="api-list">
            <h3>📡 可用 API 端点:</h3>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/health</strong> - 健康检查
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/api/products</strong> - 获取商品数据
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/api/sales/search</strong> - 销量查询
                <br><small>参数: query, start_date, end_date</small>
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/api/sales/export</strong> - 导出30天销售数据
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/api/inventory/alerts</strong> - 库存预警
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/api/trends/analysis</strong> - 趋势分析
                <br><small>参数: item_ids, period</small>
            </div>
            
            <div class="api-item">
                <span class="method post">POST</span> <strong>/api/ai/classify</strong> - AI商品分类
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span> <strong>/docs</strong> - API 文档 (Swagger)
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
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "features": {
            "clover_api": bool(os.environ.get("CLOVER_API_KEY")),
            "gemini_ai": bool(os.environ.get("GEMINI_API_KEY")),
            "data_engine": True,
            "inventory_alerts": True,
            "trend_analysis": True
        }
    }

@app.get("/api/products")
async def get_products():
    """获取商品数据"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        
        if inventory is None:
            raise HTTPException(status_code=500, detail="Failed to fetch inventory from Clover API")
        
        return {
            "products": inventory,
            "count": len(inventory),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales/search")
async def search_sales(
    query: str = Query(..., description="搜索关键词"),
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)")
):
    """销量查询API"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        # 搜索匹配的商品
        matched_items = []
        for item in inventory:
            if (query.lower() in item.get('name', '').lower() or 
                query.lower() in item.get('sku', '').lower() or
                query.lower() in item.get('code', '').lower()):
                matched_items.append(item)
        
        if not matched_items:
            raise HTTPException(status_code=404, detail="No matching products found")
        
        # 获取销售数据
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        
        item_ids = [item['id'] for item in matched_items]
        raw_sales = api.fetch_targeted_sales(item_ids, start_ts, end_ts)
        
        if raw_sales is None:
            raise HTTPException(status_code=500, detail="Failed to fetch sales data")
        
        # 处理数据
        df = data_engine.audit_process(query, matched_items, raw_sales)
        
        return {
            "query": query,
            "period": f"{start_date} to {end_date}",
            "matched_products": len(matched_items),
            "sales_records": len(raw_sales) if raw_sales else 0,
            "results": df.to_dict('records') if not df.empty else [],
            "summary": {
                "total_quantity": float(df['区间销量'].sum()) if not df.empty else 0,
                "total_revenue": df['销售总额'].str.replace('$', '').str.replace(',', '').astype(float).sum() if not df.empty else 0
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sales/export")
async def export_sales():
    """导出近30天销售数据"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        # 获取近30天数据
        start_30 = datetime.now() - timedelta(days=30)
        s_ts_30 = int(time.mktime(start_30.timetuple()) * 1000)
        e_ts_30 = int(time.mktime(datetime.now().timetuple()) * 1000)
        
        raw_sales_all = api.fetch_full_period_sales(s_ts_30, e_ts_30)
        
        if raw_sales_all is None:
            raise HTTPException(status_code=500, detail="Failed to fetch sales data")
        
        if not raw_sales_all:
            return {"message": "No sales records in the last 30 days", "data": []}
        
        # 处理导出数据
        export_df = data_engine.prepare_export_csv(inventory, raw_sales_all)
        
        return {
            "period": f"{start_30.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            "total_records": len(raw_sales_all),
            "total_products": len(export_df),
            "data": export_df.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory/alerts")
async def get_inventory_alerts():
    """库存预警API"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        alert_system = InventoryAlert(api)
        alerts_df = alert_system.check_inventory_status(inventory)
        
        return {
            "total_products": len(inventory),
            "alerts_count": len(alerts_df) if not alerts_df.empty else 0,
            "alerts": alerts_df.to_dict('records') if not alerts_df.empty else [],
            "summary": {
                "out_of_stock": len(alerts_df[alerts_df['状态'] == '缺货']) if not alerts_df.empty else 0,
                "low_stock": len(alerts_df[alerts_df['状态'] == '低库存']) if not alerts_df.empty else 0,
                "need_attention": len(alerts_df[alerts_df['状态'] == '需关注']) if not alerts_df.empty else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends/analysis")
async def analyze_trends(
    item_ids: str = Query(..., description="商品ID列表，逗号分隔"),
    period: str = Query("mom", description="分析周期: mom (月环比) 或 yoy (年同比)")
):
    """趋势分析API"""
    try:
        api = get_api_handler()
        item_id_list = item_ids.split(',')
        
        # 设置时间范围
        current_end = datetime.now()
        current_start = current_end - timedelta(days=30)
        
        trend_analyzer = TrendAnalysis(api)
        analysis_result = trend_analyzer.compare_periods(item_id_list, current_start, current_end, period)
        
        if analysis_result is None:
            raise HTTPException(status_code=400, detail="Invalid period parameter")
        
        return {
            "period_type": period,
            "current_period": f"{current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}",
            "analysis": analysis_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/classify")
async def classify_products(product_names: List[str]):
    """AI商品分类API"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        ai_manager = ProductAIManager(api)
        
        # 模拟AI分类结果（实际应该调用AI引擎）
        classifications = []
        for name in product_names:
            classifications.append({
                "product_name": name,
                "category": "AI分类结果",
                "confidence": 0.85,
                "suggested_description": f"AI生成的{name}描述"
            })
        
        return {
            "classified_products": len(classifications),
            "results": classifications
        }
        
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
