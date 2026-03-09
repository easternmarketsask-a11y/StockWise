from datetime import datetime, timedelta
import json
import logging
import os
import time
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api_handler import CloverAPIHandler
from data_engine import DataEngine

logger = logging.getLogger(__name__)
app = FastAPI(title="StockWise", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
except RuntimeError:
    pass

try:
    from google import genai
except Exception:
    genai = None

api_handler = None
data_engine = DataEngine()


def get_api_handler():
    global api_handler
    if api_handler is None:
        api_handler = CloverAPIHandler()
    return api_handler


def find_matched_items(inventory: List[Dict], query: str) -> List[Dict]:
    query_lower = query.lower().strip()
    return [
        item
        for item in inventory
        if query_lower in str(item.get("name") or "").lower()
        or query_lower in str(item.get("sku") or "").lower()
        or query_lower in str(item.get("code") or "").lower()
        or query_lower in str(item.get("alt_code") or "").lower()
    ]


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def summarize_sales_records(sales_data: Optional[List[Dict]]) -> Dict:
    if not sales_data:
        return {"quantity": 0.0, "revenue": 0.0, "orders": 0}
    quantity = sum(s.get("unitQty", 0) for s in sales_data) / 1000
    revenue = sum(s.get("price", 0) for s in sales_data) / 100
    orders = len({s.get("orderId") for s in sales_data if s.get("orderId")})
    return {
        "quantity": round(quantity, 2),
        "revenue": round(revenue, 2),
        "orders": orders,
    }


def calculate_growth(current_value: float, previous_value: float):
    if previous_value == 0:
        if current_value == 0:
            return 0.0
        return None
    return round(((current_value - previous_value) / previous_value) * 100, 2)


def build_inventory_alerts(api: CloverAPIHandler, inventory: List[Dict], limit: int = 50) -> List[Dict]:
    alerts = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    start_ts = int(start_date.timestamp() * 1000)
    end_ts = int(end_date.timestamp() * 1000)

    for item in inventory[:limit]:
        recent_sales = api.fetch_targeted_sales([item["id"]], start_ts, end_ts)
        monthly_sales = round(sum(s.get("unitQty", 0) for s in recent_sales) / 1000, 2) if recent_sales else 0.0
        estimated_stock = monthly_sales

        if monthly_sales == 0:
            alert_type = "no_sales"
            suggestion = "考虑促销或下架"
        elif estimated_stock < 10:
            alert_type = "low_stock"
            suggestion = "建议尽快补货"
        else:
            continue

        alerts.append(
            {
                "商品信息": item.get("name", ""),
                "SKU": item.get("sku") or "-",
                "Product Code": item.get("code") or "-",
                "当前库存": estimated_stock,
                "月销量": monthly_sales,
                "预警类型": alert_type,
                "建议": suggestion,
            }
        )

    return alerts


def compare_period_sales(api: CloverAPIHandler, item_ids: List[str], start_date: datetime, end_date: datetime, comparison_type: str) -> Dict:
    if comparison_type == "mom":
        previous_start = start_date - timedelta(days=30)
        previous_end = end_date - timedelta(days=30)
    elif comparison_type == "yoy":
        previous_start = start_date - timedelta(days=365)
        previous_end = end_date - timedelta(days=365)
    else:
        raise ValueError("comparison_type must be mom or yoy")

    current_sales = api.fetch_targeted_sales(item_ids, int(start_date.timestamp() * 1000), int((end_date + timedelta(days=1)).timestamp() * 1000) - 1)
    previous_sales = api.fetch_targeted_sales(item_ids, int(previous_start.timestamp() * 1000), int((previous_end + timedelta(days=1)).timestamp() * 1000) - 1)
    current_summary = summarize_sales_records(current_sales)
    previous_summary = summarize_sales_records(previous_sales)

    return {
        "current_period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            **current_summary,
        },
        "previous_period": {
            "start": previous_start.strftime("%Y-%m-%d"),
            "end": previous_end.strftime("%Y-%m-%d"),
            **previous_summary,
        },
        "growth": {
            "quantity": calculate_growth(current_summary["quantity"], previous_summary["quantity"]),
            "revenue": calculate_growth(current_summary["revenue"], previous_summary["revenue"]),
            "orders": calculate_growth(current_summary["orders"], previous_summary["orders"]),
        },
    }


def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, "GEMINI_API_KEY 未配置"
    if genai is None:
        return None, "google-genai 依赖未安装"
    try:
        return genai.Client(api_key=api_key), None
    except Exception as exc:
        logger.exception("Gemini client init failed")
        return None, str(exc)


def generate_ai_json(prompt: str) -> Dict:
    client, error = get_gemini_client()
    if error:
        raise HTTPException(status_code=503, detail=error)
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = getattr(response, "text", "") or ""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"raw_response": text}
        return json.loads(text[start:end + 1])
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Gemini request failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/", response_class=HTMLResponse)
async def root():
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Eastern Market</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f3f6fb; color: #162033; }}
        .header {{ background: linear-gradient(135deg, #0f3d8c, #1e63d2); color: #fff; padding: 24px; box-shadow: 0 8px 30px rgba(15,61,140,.2); }}
        .header-inner {{ max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; gap: 16px; align-items: center; }}
        .brand {{ display: flex; align-items: center; gap: 20px; }}
        .brand img {{ height: 50px; width: auto; object-fit: contain; border-radius: 8px; background: #fff; padding: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .logo-text {{ display: flex; flex-direction: column; gap: 4px; }}
        .logo-text h1 {{ margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; }}
        .logo-text h1 .stock {{ color: #fff; }}
        .logo-text h1 .wise {{ color: #ffd700; font-weight: 800; }}
        .logo-text p {{ margin: 0; opacity: .9; font-size: 13px; }}
                .container {{ max-width: 1400px; margin: 24px auto; padding: 0 20px 40px; display: flex; gap: 24px; }}
        .sidebar {{ width: 250px; flex-shrink: 0; }}
        .main-content {{ flex-grow: 1; min-width: 0; }}
        .cards {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-bottom: 20px; }}
        .card {{ background: #fff; border-radius: 18px; padding: 18px; box-shadow: 0 10px 30px rgba(19,45,89,.08); border: 1px solid #e7edf7; }}
        .card .label {{ font-size: 12px; color: #6b7a90; text-transform: uppercase; letter-spacing: .08em; }}
        .card .value {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
        .tabs {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }}
        .tab-button {{ border: 0; background: #dfe8f8; color: #214a94; padding: 14px 16px; border-radius: 12px; cursor: pointer; font-weight: 600; text-align: left; transition: all 0.2s; }}
        .tab-button:hover {{ background: #c8d9f4; }}
        .tab-button.active {{ background: #1e63d2; color: #fff; box-shadow: 0 4px 12px rgba(30,99,210,0.2); }}
        .tab-panel {{ display: none; }}
        .tab-panel.active {{ display: block; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .grid-2 {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
        label {{ display: block; font-size: 14px; margin-bottom: 8px; color: #4f5f78; }}
        input, select, button {{ font: inherit; }}
        input, select {{ width: 100%; padding: 11px 12px; border-radius: 10px; border: 1px solid #cfd8e6; background: #fff; }}
        .btn {{ border: 0; background: #1e63d2; color: #fff; padding: 12px 16px; border-radius: 10px; cursor: pointer; font-weight: 600; }}
        .btn.secondary {{ background: #0f172a; }}
        .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }}
        .status {{ margin-top: 12px; font-size: 14px; color: #51627c; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }}
        .metric {{ background: #f8fbff; border: 1px solid #e3ecf8; border-radius: 14px; padding: 16px; }}
        .metric .k {{ font-size: 12px; color: #6b7a90; }}
        .metric .v {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
        table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 14px; overflow: hidden; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #edf2fa; text-align: left; font-size: 14px; vertical-align: top; }}
        th {{ background: #f7faff; color: #4e607a; }}
        .panel-title {{ margin: 0 0 14px; font-size: 22px; }}
        .muted {{ color: #6b7a90; font-size: 14px; }}
        .footer {{ text-align: center; color: #7a879b; font-size: 13px; margin-top: 24px; }}
        .error {{ color: #c62828; }}
        .success {{ color: #2e7d32; }}
        pre {{ background: #0f172a; color: #e2e8f0; border-radius: 14px; padding: 16px; overflow: auto; }}
        @media (max-width: 900px) {{ .container {{ flex-direction: column; }} .sidebar {{ width: 100%; }} .tabs {{ flex-direction: row; flex-wrap: wrap; }} .tab-button {{ flex: 1 1 auto; text-align: center; }} .cards, .grid-2, .grid-3, .metrics {{ grid-template-columns: 1fr; }} .header-inner {{ flex-direction: column; align-items: flex-start; }} }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <div class="brand">
                <img src="/assets/eastern_market_logo.jpeg" alt="Eastern Market" onerror="this.style.display='none'">
                <div class="logo-text">
                    <h1><span class="stock">Stock</span><span class="wise">Wise</span></h1>
                    <p>Eastern Market 商品销量分析系统 · FastAPI + HTML/JS</p>
                </div>
            </div>
        </div>
    </header>
    <main class="container">
        <aside class="sidebar">
            <section class="tabs">
                <button class="tab-button active" data-tab="sales">🔍 销量分析查询</button>
                <button class="tab-button" data-tab="charts">📊 数据可视化</button>
                <button class="tab-button" data-tab="alerts">📊 库存预警监控</button>
                <button class="tab-button" data-tab="trends">📈 销售趋势分析</button>
                <button class="tab-button" data-tab="ai" style="opacity: 0.7; font-size: 0.9em;">🤖 智能管理</button>
            </section>
        </aside>
        <div class="main-content">
            <!-- 可折叠的系统信息区域 -->
            <div style="margin-bottom: 20px; text-align: right;">
                <button id="toggleSystemInfo" style="background: none; border: 1px solid #dfe8f8; color: #6b7a90; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">
                    📋 系统信息 ▼
                </button>
            </div>
            <div id="systemInfoCards" class="cards" style="display: none;">
                <div class="card"><div class="label">Version</div><div class="value">v2.1.0</div></div>
                <div class="card"><div class="label">UI Stack</div><div class="value">HTML / JS</div></div>
                <div class="card"><div class="label">API Docs</div><div class="value"><a href="/docs">/docs</a></div></div>
            </div>
        <section id="sales" class="tab-panel active card">
            <h2 class="panel-title">🔍 销量分析查询</h2>
            <p class="muted">按名称、SKU、Code、条码搜索，指定日期范围后查看结果并导出 CSV。</p>
            <div class="grid-3">
                <div><label for="query">搜索关键词</label><input id="query" placeholder="输入名称、SKU、Code 或条码片段"></div>
                <div><label for="start_date">开始日期</label><input id="start_date" type="date"></div>
                <div><label for="end_date">结束日期</label><input id="end_date" type="date"></div>
            </div>
            <div class="actions"><button class="btn" id="searchButton">开始查询</button><button class="btn secondary" id="exportButton" style="opacity: 0.8; font-size: 0.9em;">📊 导出近 30 天 CSV</button></div>
            <div id="salesStatus" class="status"></div>
            <div id="salesMetrics" class="metrics"></div>
            <div id="salesResults"></div>
        </section>
        <section id="charts" class="tab-panel card">
            <h2 class="panel-title">📊 数据可视化</h2>
            <p class="muted">基于最近一次查询结果自动绘图。</p>
            <div class="grid-2"><div class="card"><canvas id="qtyChart"></canvas></div><div class="card"><canvas id="revenueChart"></canvas></div></div>
            <div class="status" id="chartStatus">请先在“销量分析查询”中完成一次查询。</div>
        </section>
        <section id="alerts" class="tab-panel card">
            <h2 class="panel-title">📊 库存预警监控</h2>
            <p class="muted">自动扫描缺货、低库存与无销量商品。</p>
            <div class="actions"><button class="btn" id="loadAlertsButton">刷新预警</button></div>
            <div id="alertMetrics" class="metrics"></div>
            <div id="alertStatus" class="status"></div>
            <div id="alertResults"></div>
        </section>
        <section id="trends" class="tab-panel card">
            <h2 class="panel-title">📈 销售趋势分析</h2>
            <p class="muted">支持月环比与年同比。</p>
            <div class="grid-2">
                <div><label for="trendQuery">商品关键词</label><input id="trendQuery" placeholder="输入商品关键词，留空则使用前 10 个商品"></div>
                <div><label for="trendType">对比类型</label><select id="trendType"><option value="mom">月环比</option><option value="yoy">年同比</option></select></div>
            </div>
            <div class="grid-2" style="margin-top: 16px;">
                <div><label for="trendStartDate">开始日期</label><input id="trendStartDate" type="date"></div>
                <div><label for="trendEndDate">结束日期</label><input id="trendEndDate" type="date"></div>
            </div>
            <div class="actions"><button class="btn" id="loadTrendButton">分析趋势</button></div>
            <div id="trendStatus" class="status"></div>
            <div id="trendMetrics" class="metrics"></div>
            <div id="trendResults"></div>
        </section>
        <section id="ai" class="tab-panel card">
            <h2 class="panel-title">🤖 智能管理</h2>
            <p class="muted">Gemini AI 商品分类与描述生成。未配置密钥时页面仍可访问，但接口会返回提示。</p>
            <div class="grid-2">
                <div><label for="aiProductName">商品名称</label><input id="aiProductName" placeholder="例如 Fuji Apple"></div>
                <div><label for="aiProductPrice">价格</label><input id="aiProductPrice" type="number" step="0.01" placeholder="0.00"></div>
            </div>
            <div class="grid-2" style="margin-top: 16px;">
                <div><label for="aiProductSku">SKU</label><input id="aiProductSku" placeholder="可选"></div>
                <div><label for="aiProductCode">Code</label><input id="aiProductCode" placeholder="可选"></div>
            </div>
            <div class="grid-2" style="margin-top: 16px;">
                <div><label for="descLength">描述长度</label><select id="descLength"><option value="short">简短</option><option value="medium" selected>中等</option><option value="long">详细</option></select></div>
                <div></div>
            </div>
            <div class="actions"><button class="btn" id="classifyButton">智能分类</button><button class="btn secondary" id="describeButton">生成描述</button></div>
            <div id="aiStatus" class="status"></div>
            <div id="aiResults"></div>
        </section>
        </div>
    </main>
    <div class="footer">Copyright © 2026 EasternMarket. All rights reserved.</div>
    <script>
        const tabs = document.querySelectorAll('.tab-button');
        const panels = document.querySelectorAll('.tab-panel');
        const state = { lastQueryResults: [] };
        let qtyChart = null;
        let revenueChart = null;

        function setDefaultDates() {
            const today = new Date();
            const start = new Date();
            start.setDate(today.getDate() - 30);
            const fmt = (date) => date.toISOString().slice(0, 10);
            document.getElementById('start_date').value = fmt(start);
            document.getElementById('end_date').value = fmt(today);
            document.getElementById('trendStartDate').value = fmt(start);
            document.getElementById('trendEndDate').value = fmt(today);
        }

        tabs.forEach(button => button.addEventListener('click', () => {
            tabs.forEach(tab => tab.classList.remove('active'));
            panels.forEach(panel => panel.classList.remove('active'));
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        }));

        function setStatus(id, message, type='') {
            const el = document.getElementById(id);
            el.className = `status ${type}`;
            el.textContent = message || '';
        }

        function renderMetrics(id, items) {
            const container = document.getElementById(id);
            container.innerHTML = items.map(item => `<div class="metric"><div class="k">${{item.label}}</div><div class="v">${{item.value}}</div></div>`).join('');
        }

        function renderTable(containerId, rows) {
            const container = document.getElementById(containerId);
            if (!rows || !rows.length) {
                container.innerHTML = '<p class="muted">暂无数据。</p>';
                return;
            }
            const headers = Object.keys(rows[0]);
            container.innerHTML = `<table><thead><tr>${{headers.map(h => `<th>${{h}}</th>`).join('')}}</tr></thead><tbody>${{rows.map(row => `<tr>${{headers.map(h => `<td>${{row[h] ?? ''}}</td>`).join('')}}</tr>`).join('')}}</tbody></table>`;
        }

        async function requestJson(url, options) {
            const response = await fetch(url, options);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.message || '请求失败');
            }
            return data;
        }

        function drawCharts(rows) {
            const labels = rows.map(row => row['商品信息']);
            const qtyData = rows.map(row => Number(row['区间销量']) || 0);
            const revenueData = rows.map(row => Number(String(row['销售总额']).replace('$', '').replace(/,/g,'')) || 0);
            if (qtyChart) qtyChart.destroy();
            if (revenueChart) revenueChart.destroy();
            qtyChart = new Chart(document.getElementById('qtyChart'), { type: 'bar', data: { labels, datasets: [{ label: '销量', data: qtyData, backgroundColor: '#1e63d2' }] }, options: { responsive: true, plugins: { legend: { display: false } } } });
            revenueChart = new Chart(document.getElementById('revenueChart'), { type: 'doughnut', data: { labels, datasets: [{ label: '销售额', data: revenueData, backgroundColor: ['#1e63d2','#4f8df0','#7aacff','#99bfff','#bfd7ff','#dce9ff'] }] }, options: { responsive: true } });
            setStatus('chartStatus', `已根据最近查询结果绘制 ${{rows.length}} 个商品的图表。`, 'success');
        }

        document.getElementById('searchButton').addEventListener('click', async () => {
            const query = document.getElementById('query').value.trim();
            const startDate = document.getElementById('start_date').value;
            const endDate = document.getElementById('end_date').value;
            if (!query) { setStatus('salesStatus', '请输入搜索关键词。', 'error'); return; }
            setStatus('salesStatus', '正在查询...');
            try {
                const data = await requestJson(`/api/sales/search?query=${{encodeURIComponent(query)}}&start_date=${{startDate}}&end_date=${{endDate}}`);
                state.lastQueryResults = data.results || [];
                renderMetrics('salesMetrics', [
                    { label: '匹配商品', value: data.matched_products },
                    { label: '销售记录', value: data.sales_records },
                    { label: '总销量', value: data.summary.total_quantity },
                    { label: '总销售额', value: '$' + Number(data.summary.total_revenue || 0).toFixed(2) },
                ]);
                renderTable('salesResults', state.lastQueryResults);
                setStatus('salesStatus', `查询成功：${{data.period}}`, 'success');
                if (state.lastQueryResults.length) drawCharts(state.lastQueryResults);
            } catch (error) {
                renderMetrics('salesMetrics', []);
                renderTable('salesResults', []);
                setStatus('salesStatus', error.message, 'error');
            }
        });

        document.getElementById('exportButton').addEventListener('click', async () => {
            setStatus('salesStatus', '正在准备导出数据...');
            try {
                const data = await requestJson('/api/sales/export');
                const rows = data.data || [];
                if (!rows.length) { setStatus('salesStatus', '近 30 天没有销售记录。', 'error'); return; }
                const headers = Object.keys(rows[0]);
                const csv = [headers.join(','), ...rows.map(row => headers.map(h => `"${{String(row[h] ?? '').replaceAll('"','""')}}"`).join(','))].join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'Sales_Summary.csv';
                link.click();
                setStatus('salesStatus', 'CSV 已开始下载。', 'success');
            } catch (error) {
                setStatus('salesStatus', error.message, 'error');
            }
        });

        document.getElementById('loadAlertsButton').addEventListener('click', async () => {
            setStatus('alertStatus', '正在扫描库存预警...');
            try {
                const data = await requestJson('/api/inventory/alerts');
                renderMetrics('alertMetrics', [
                    { label: '缺货', value: data.summary.out_of_stock },
                    { label: '低库存', value: data.summary.low_stock },
                    { label: '无销量', value: data.summary.no_sales },
                    { label: '需关注', value: data.summary.total_alerts },
                ]);
                renderTable('alertResults', data.alerts || []);
                setStatus('alertStatus', '库存预警扫描完成。', 'success');
            } catch (error) {
                setStatus('alertStatus', error.message, 'error');
            }
        });

        document.getElementById('loadTrendButton').addEventListener('click', async () => {
            const query = document.getElementById('trendQuery').value.trim();
            const period = document.getElementById('trendType').value;
            const startDate = document.getElementById('trendStartDate').value;
            const endDate = document.getElementById('trendEndDate').value;
            setStatus('trendStatus', '正在分析趋势...');
            try {
                const params = new URLSearchParams({{ period, start_date: startDate, end_date: endDate }});
                if (query) params.set('query', query);
                const data = await requestJson(`/api/trends/analysis?${{params.toString()}}`);
                renderMetrics('trendMetrics', [
                    { label: '本期销量', value: data.current_period.quantity },
                    { label: '本期销售额', value: '$' + Number(data.current_period.revenue).toFixed(2) },
                    { label: '上期销量', value: data.previous_period.quantity },
                    { label: '上期销售额', value: '$' + Number(data.previous_period.revenue).toFixed(2) },
                ]);
                renderTable('trendResults', [
                    { 指标: '销量', 本期: data.current_period.quantity, 上期: data.previous_period.quantity, 增长率: data.growth.quantity === null ? '∞' : data.growth.quantity + '%' },
                    { 指标: '销售额', 本期: '$' + Number(data.current_period.revenue).toFixed(2), 上期: '$' + Number(data.previous_period.revenue).toFixed(2), 增长率: data.growth.revenue === null ? '∞' : data.growth.revenue + '%' },
                    { 指标: '订单数', 本期: data.current_period.orders, 上期: data.previous_period.orders, 增长率: data.growth.orders === null ? '∞' : data.growth.orders + '%' },
                ]);
                setStatus('trendStatus', `趋势分析完成：${{data.comparison_type === 'mom' ? '月环比' : '年同比'}}`, 'success');
            } catch (error) {
                setStatus('trendStatus', error.message, 'error');
            }
        });

        function buildAiPayload() {
            return {
                name: document.getElementById('aiProductName').value.trim(),
                sku: document.getElementById('aiProductSku').value.trim(),
                code: document.getElementById('aiProductCode').value.trim(),
                price: Number(document.getElementById('aiProductPrice').value || 0),
            };
        }

        document.getElementById('classifyButton').addEventListener('click', async () => {
            const payload = buildAiPayload();
            if (!payload.name) { setStatus('aiStatus', '请输入商品名称。', 'error'); return; }
            setStatus('aiStatus', 'AI 正在分类...');
            try {
                const data = await requestJson('/api/ai/classify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                document.getElementById('aiResults').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                setStatus('aiStatus', '分类完成。', 'success');
            } catch (error) {
                setStatus('aiStatus', error.message, 'error');
            }
        });

        document.getElementById('describeButton').addEventListener('click', async () => {
            const payload = buildAiPayload();
            payload.target_length = document.getElementById('descLength').value;
            if (!payload.name) { setStatus('aiStatus', '请输入商品名称。', 'error'); return; }
            setStatus('aiStatus', 'AI 正在生成描述...');
            try {
                const data = await requestJson('/api/ai/describe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                document.getElementById('aiResults').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                setStatus('aiStatus', '描述生成完成。', 'success');
            } catch (error) {
                setStatus('aiStatus', error.message, 'error');
            }
        });

        // 系统信息折叠功能
        document.getElementById('toggleSystemInfo').addEventListener('click', () => {
            const cards = document.getElementById('systemInfoCards');
            const button = document.getElementById('toggleSystemInfo');
            if (cards.style.display === 'none') {
                cards.style.display = 'grid';
                button.textContent = '📋 系统信息 ▲';
            } else {
                cards.style.display = 'none';
                button.textContent = '📋 系统信息 ▼';
            }
        });

        setDefaultDates();
    </script>
</body>
</html>'''


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "StockWise",
        "version": "2.1.0",
        "cloud_run": {
            "service": os.environ.get("K_SERVICE"),
            "revision": os.environ.get("K_REVISION"),
            "configuration": os.environ.get("K_CONFIGURATION"),
        },
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "features": {
            "clover_api": bool(os.environ.get("CLOVER_API_KEY")),
            "data_engine": True,
            "gemini_ai": bool(os.environ.get("GEMINI_API_KEY")),
        },
    }


@app.get("/api/products")
async def get_products():
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if inventory is None:
            raise HTTPException(status_code=500, detail="Failed to fetch inventory from Clover API")
        return {"products": inventory, "count": len(inventory), "last_updated": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sales/search")
async def search_sales(
    query: str = Query(..., description="搜索关键词"),
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
):
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        matched_items = find_matched_items(inventory, query)
        if not matched_items:
            raise HTTPException(status_code=404, detail="No matching products found")
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
        end_ts = int((datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000) - 1
        raw_sales = api.fetch_targeted_sales([item["id"] for item in matched_items], start_ts, end_ts)
        if raw_sales is None:
            raise HTTPException(status_code=500, detail="Failed to fetch sales data")
        df = data_engine.audit_process(query, matched_items, raw_sales)
        return {
            "query": query,
            "period": f"{start_date} to {end_date}",
            "matched_products": len(matched_items),
            "sales_records": len(raw_sales) if raw_sales else 0,
            "results": df.to_dict("records") if not df.empty else [],
            "summary": {
                "total_quantity": float(df["区间销量"].sum()) if not df.empty else 0,
                "total_revenue": df["销售总额"].str.replace("$", "").str.replace(",", "").astype(float).sum() if not df.empty else 0,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sales/export")
async def export_sales():
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        start_30 = datetime.now() - timedelta(days=30)
        s_ts_30 = int(time.mktime(start_30.timetuple()) * 1000)
        e_ts_30 = int(time.mktime(datetime.now().timetuple()) * 1000)
        raw_sales_all = api.fetch_full_period_sales(s_ts_30, e_ts_30)
        if raw_sales_all is None:
            raise HTTPException(status_code=500, detail="Failed to fetch sales data")
        if not raw_sales_all:
            return {"message": "No sales records in the last 30 days", "data": []}
        export_df = data_engine.prepare_export_csv(inventory, raw_sales_all)
        return {
            "period": f"{start_30.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            "total_records": len(raw_sales_all),
            "total_products": len(export_df),
            "data": export_df.to_dict("records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inventory/alerts")
async def inventory_alerts(limit: int = Query(50, ge=1, le=200)):
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        alerts = build_inventory_alerts(api, inventory, limit=limit)
        summary = {
            "out_of_stock": len([a for a in alerts if a["预警类型"] == "out_of_stock"]),
            "low_stock": len([a for a in alerts if a["预警类型"] == "low_stock"]),
            "no_sales": len([a for a in alerts if a["预警类型"] == "no_sales"]),
            "total_alerts": len(alerts),
        }
        return {"alerts": alerts, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends/analysis")
async def trends_analysis(
    period: str = Query("mom", pattern="^(mom|yoy)$"),
    start_date: str = Query(...),
    end_date: str = Query(...),
    query: Optional[str] = Query(None),
):
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        matched_items = find_matched_items(inventory, query) if query else inventory[:10]
        if not matched_items:
            raise HTTPException(status_code=404, detail="No matching products found")
        result = compare_period_sales(
            api,
            [item["id"] for item in matched_items],
            datetime.strptime(start_date, "%Y-%m-%d"),
            datetime.strptime(end_date, "%Y-%m-%d"),
            period,
        )
        result["comparison_type"] = period
        result["matched_products"] = len(matched_items)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/classify")
async def ai_classify(payload: Dict):
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")
    prompt = f'''请对以下商品进行智能分类，返回严格 JSON：
{{
  "main_category": "主类别",
  "sub_category": "子类别",
  "attributes": ["属性1", "属性2"],
  "target_customers": ["目标客户1"],
  "storage_requirements": "存储要求",
  "confidence_score": 0.95
}}
商品名称: {name}
SKU: {payload.get("sku", "")}
Code: {payload.get("code", "")}
价格: ${safe_float(payload.get("price", 0)):.2f}
'''
    return generate_ai_json(prompt)


@app.post("/api/ai/describe")
async def ai_describe(payload: Dict):
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")
    target_length = str(payload.get("target_length") or "medium")
    prompt = f'''请为以下商品生成营销描述，返回严格 JSON：
{{
  "description": "商品描述",
  "keywords": ["关键词1", "关键词2"],
  "selling_points": ["卖点1", "卖点2"],
  "usage_suggestions": "使用建议",
  "confidence_score": 0.90
}}
商品名称: {name}
SKU: {payload.get("sku", "")}
Code: {payload.get("code", "")}
价格: ${safe_float(payload.get("price", 0)):.2f}
描述长度: {target_length}
'''
    return generate_ai_json(prompt)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
