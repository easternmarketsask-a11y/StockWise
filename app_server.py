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

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Eastern Market</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f6f8fc; color: #162033; }
        .header { background: rgba(255,255,255,.94); color: #162033; padding: 18px 24px; border-bottom: 1px solid #e6ecf5; position: sticky; top: 0; z-index: 20; backdrop-filter: blur(10px); }
        .header-inner { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; gap: 16px; align-items: center; }
        .brand { display: flex; align-items: center; gap: 14px; min-width: 0; }
        .brand-mark { width: 64px; height: 64px; border-radius: 18px; background: #ffffff; border: 1px solid #e3eaf5; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0; }
        .brand-mark img { width: 100%; height: 100%; object-fit: contain; padding: 8px; display: block; }
        .brand-mark-fallback { display: none; align-items: center; justify-content: center; width: 100%; height: 100%; font-size: 18px; font-weight: 800; letter-spacing: .06em; color: #1e63d2; background: linear-gradient(135deg, #f8fbff, #eef4ff); }
        .brand-copy { min-width: 0; }
        .brand-kicker { margin: 0 0 4px; font-size: 12px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #64748b; }
        .brand h1 { margin: 0; font-size: 30px; line-height: 1.1; color: #1e63d2; letter-spacing: -0.03em; text-align: center; }
        .brand p { margin: 6px 0 0; color: #64748b; font-size: 14px; }
        .header-badge { display: inline-flex; align-items: center; padding: 8px 12px; border-radius: 999px; border: 1px solid #dbe6f5; background: #f8fbff; color: #4f5f78; font-size: 12px; font-weight: 700; white-space: nowrap; }
        .container { max-width: 1360px; margin: 20px auto; padding: 0 20px 36px; display: flex; gap: 20px; }
        .sidebar { width: 250px; flex-shrink: 0; }
        .sidebar-shell { position: sticky; top: 96px; background: #fff; border: 1px solid #e7edf7; border-radius: 18px; padding: 16px; box-shadow: 0 6px 18px rgba(19,45,89,.04); }
        .sidebar-label { margin: 0 0 10px; font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #64748b; }
        .main-content { flex-grow: 1; min-width: 0; }
        .cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
        .card { background: #fff; border-radius: 18px; padding: 18px; box-shadow: 0 6px 18px rgba(19,45,89,.05); border: 1px solid #e7edf7; }
        .card .label { font-size: 12px; color: #6b7a90; text-transform: uppercase; letter-spacing: .08em; }
        .card .value { font-size: 24px; font-weight: 700; margin-top: 6px; }
        label { display: block; font-size: 13px; margin-bottom: 8px; color: #4f5f78; font-weight: 600; }
        input, select { width: 100%; padding: 11px 12px; border-radius: 12px; border: 1px solid #d3ddec; background: #fff; transition: border-color .2s ease, box-shadow .2s ease, background-color .2s ease; }
        input:focus, select:focus { outline: none; border-color: #8eb4f3; box-shadow: 0 0 0 4px rgba(30,99,210,.10); }
        .btn { border: 0; background: #1e63d2; color: #fff; padding: 11px 16px; border-radius: 12px; cursor: pointer; font-weight: 600; box-shadow: 0 4px 12px rgba(30,99,210,.16); transition: transform .15s ease, box-shadow .15s ease, opacity .15s ease; }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(30,99,210,.18); }
        .btn.secondary { background: #eef4ff; color: #214a94; box-shadow: none; border: 1px solid #d8e3f7; }
        .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
        .status { margin-top: 12px; font-size: 14px; color: #51627c; min-height: 20px; padding: 10px 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; }
        .status.info { color: #38517a; background: #f8fbff; border-color: #dbe7f8; }
        .status.success { color: #256c3b; background: #edf9f1; border-color: #cfead8; }
        .status.error { color: #b42318; background: #fef3f2; border-color: #f3d1cc; }
        .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }
        table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 14px; overflow: hidden; }
        th, td { padding: 12px; border-bottom: 1px solid #edf2fa; text-align: left; font-size: 14px; vertical-align: top; }
        th { background: #f7faff; color: #4e607a; }
        .hero-card { padding: 20px; }
        .hero-title { font-size: 24px; font-weight: 700; margin: 0 0 8px; letter-spacing: -0.03em; }
        .hero-subtitle { margin: 0; color: #5b6b82; line-height: 1.6; max-width: 720px; }
        .hero-note { margin-top: 12px; color: #7a879b; font-size: 13px; }
        .tabs { display: flex; flex-direction: column; gap: 8px; }
        .tab-button { border: 1px solid transparent; background: #f8fbff; color: #42526b; padding: 13px 14px; border-radius: 14px; cursor: pointer; font-weight: 700; text-align: left; transition: all .18s ease; }
        .tab-button:hover { background: #f2f7ff; border-color: #d9e5f6; color: #214a94; }
        .tab-button.active { background: linear-gradient(135deg, #1e63d2, #2b74ea); color: #fff; border-color: #1e63d2; box-shadow: 0 10px 20px rgba(30,99,210,.18); }
        .tab-panel { display: none; }
        .tab-panel.active { display: block; }
        .panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid #edf2fa; }
        .panel-copy { min-width: 0; }
        .panel-kicker { margin: 0 0 6px; font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #64748b; }
        .panel-meta { display: inline-flex; align-items: center; padding: 8px 12px; border-radius: 999px; border: 1px solid #dbe6f5; background: #f8fbff; color: #4f5f78; font-size: 12px; font-weight: 700; white-space: nowrap; }
        .quick-actions, .quick-filters, .inline-actions, .tag-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .section-gap { margin-top: 16px; }
        .section-gap-sm { margin-top: 12px; }
        .chip { border: 1px solid #d8e3f7; background: #f8fbff; color: #214a94; padding: 8px 12px; border-radius: 999px; cursor: pointer; font-size: 13px; font-weight: 600; }
        .chip.active { background: #1e63d2; color: #fff; border-color: #1e63d2; }
        .search-layout { display: grid; grid-template-columns: 1.35fr .85fr; gap: 14px; align-items: start; }
        .workspace-card { min-height: 100%; }
        .product-list { display: grid; gap: 12px; margin-top: 14px; }
        .product-item { background: #fff; border: 1px solid #e5edf9; border-radius: 16px; padding: 14px; box-shadow: 0 4px 14px rgba(19,45,89,.04); }
        .product-top { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
        .product-main { flex: 1; min-width: 0; }
        .product-actions { width: 220px; flex-shrink: 0; }
        .product-title { margin: 0; font-size: 17px; line-height: 1.35; }
        .meta { color: #64748b; font-size: 13px; margin-top: 4px; }
        .status-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        .badge { padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #eef4ff; color: #214a94; }
        .badge.warn { background: #fff4e5; color: #b26b00; }
        .badge.success { background: #e9f8ef; color: #2e7d32; }
        .selection-box { display: flex; align-items: center; gap: 10px; }
        .selection-box input { width: auto; }
        .insight-list { display: grid; gap: 10px; margin-top: 14px; }
        .insight-item { border: 1px solid #e8eef8; border-radius: 12px; padding: 12px; background: #f9fbff; }
        .overview-list { display: grid; gap: 10px; margin-top: 12px; }
        .overview-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border: 1px solid #e8eef8; border-radius: 14px; background: #fbfdff; }
        .overview-item strong { font-size: 13px; color: #42526b; }
        .overview-value { font-size: 13px; color: #162033; font-weight: 700; text-align: right; }
        .detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
        .detail-section { border: 1px solid #e8eef8; border-radius: 16px; padding: 16px; background: #fbfdff; }
        .detail-section h3 { margin: 0 0 14px; }
        .detail-row { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid #eef3fb; }
        .detail-row:last-child { border-bottom: 0; }
        .detail-key { color: #64748b; font-size: 13px; }
        .detail-value { font-weight: 600; text-align: right; }
        .detail-value-text { font-weight: 600; text-align: left; line-height: 1.6; white-space: pre-wrap; }
        .detail-block { margin-top: 12px; }
        .library-list, .batch-list { display: grid; gap: 12px; margin-top: 16px; }
        .library-item, .batch-item { border: 1px solid #e5edf9; border-radius: 14px; padding: 14px; background: #fff; }
        .empty-state { border: 1px dashed #cdd9ec; border-radius: 16px; padding: 24px; text-align: center; color: #64748b; background: #fafcff; }
        .empty-state strong { display: block; margin-bottom: 6px; color: #42526b; font-size: 15px; }
        .muted-small { color: #7a879b; font-size: 12px; }
        .two-column-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
        .progress-bar { width: 100%; height: 8px; background: #e8eef8; border-radius: 999px; overflow: hidden; margin: 12px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #1e63d2, #2b74ea); transition: width 0.3s ease; border-radius: 999px; }
        .progress-text { font-size: 13px; color: #64748b; margin-top: 6px; text-align: center; }
        .btn-icon { padding: 8px 12px; background: transparent; border: 1px solid #d8e3f7; color: #64748b; border-radius: 10px; cursor: pointer; font-size: 16px; transition: all 0.2s; }
        .btn-icon:hover { background: #f8fbff; border-color: #1e63d2; color: #1e63d2; }
        .dropdown-menu { position: absolute; right: 0; top: 100%; margin-top: 4px; background: #fff; border: 1px solid #e7edf7; border-radius: 12px; box-shadow: 0 8px 24px rgba(19,45,89,.12); padding: 6px; min-width: 160px; z-index: 10; display: none; }
        .dropdown-menu.show { display: block; }
        .dropdown-item { padding: 10px 12px; border-radius: 8px; cursor: pointer; font-size: 14px; color: #42526b; transition: background 0.15s; }
        .dropdown-item:hover { background: #f8fbff; color: #1e63d2; }
        .product-actions { position: relative; display: flex; gap: 8px; align-items: center; }
        .empty-state-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.3; }
        .grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
        @media (max-width: 900px) { .container { flex-direction: column; } .sidebar { width: 100%; } .sidebar-shell { position: static; padding: 14px; } .tabs { flex-direction: row; flex-wrap: wrap; } .tab-button { flex: 1 1 auto; text-align: center; } .cards, .grid-2, .grid-3, .metrics, .hero, .search-layout, .detail-grid { grid-template-columns: 1fr; } .header-inner { flex-direction: column; align-items: flex-start; } .header { padding: 16px 18px; } .header-badge, .panel-meta { display: none; } .panel-header { padding-bottom: 12px; margin-bottom: 16px; } .product-top { flex-direction: column; } .product-actions { width: 100%; } .two-column-actions { grid-template-columns: 1fr 1fr; } }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <div class="brand">
                <div class="brand-mark">
                    <img id="brandLogo" src="/assets/eastern_market_logo.jpeg" alt="Eastern Market Logo">
                    <div id="brandLogoFallback" class="brand-mark-fallback">EM</div>
                </div>
                <div class="brand-copy">
                    <div class="brand-kicker">Eastern Market</div>
                    <h1>StockWise</h1>
                    <p>商品销量分析与运营助手</p>
                </div>
            </div>
            <div class="header-badge">Internal Business Tool</div>
        </div>
    </header>
    <main class="container">
        <aside class="sidebar">
            <div class="sidebar-shell">
                <div class="sidebar-label">导航</div>
                <section class="tabs">
                    <button class="tab-button active" data-tab="products">📦 销量查询</button>
                    <button class="tab-button" data-tab="categories">📂 商品分类</button>
                    <button class="tab-button" data-tab="batch">⚙️ 批量处理</button>
                    <button class="tab-button" data-tab="analytics">📊 数据分析</button>
                </section>
            </div>
        </aside>
        <div class="main-content">
        <section id="products" class="tab-panel active card">
            <div class="panel-header">
                <div class="panel-copy">
                    <div class="panel-kicker">Product Management</div>
                    <h2 class="panel-title">🔍 销量查询</h2>
                    <p class="muted">搜索商品、查看销量数据、执行 AI 分类和描述生成。所有核心操作都在这里完成。</p>
                </div>
                <div class="panel-meta">搜索 · AI 处理 · 结果查看</div>
            </div>
            <div class="search-layout">
                <div>
                    <div class="grid-3">
                        <div><label for="query">搜索关键词</label><input id="query" placeholder="输入商品名、SKU、Code 或条码片段"></div>
                        <div><label for="searchMode">搜索方式</label><select id="searchMode"><option value="all">全部字段</option><option value="name">商品名</option><option value="sku">SKU</option><option value="code">Code/条码</option></select></div>
                        <div><label for="start_date">时间范围</label><input id="start_date" type="date"></div>
                    </div>
                    <div class="grid-3 section-gap">
                        <div><label for="end_date">结束日期</label><input id="end_date" type="date"></div>
                        <div><label for="statusFilter">状态筛选</label><select id="statusFilter"><option value="all">全部商品</option><option value="pending_classify">待分类</option><option value="pending_describe">待描述</option><option value="completed">已完成</option></select></div>
                        <div><label>快捷筛选</label><div class="quick-filters"><button class="chip" data-days="7">近7天</button><button class="chip active" data-days="30">近30天</button><button class="chip" data-days="90">近90天</button></div></div>
                    </div>
                    <div class="actions"><button class="btn" id="searchButton">搜索商品</button><button class="btn secondary" id="exportButton">导出近 30 天 CSV</button></div>
                </div>
                <div class="card workspace-card">
                    <div class="label">快速操作</div>
                    <div id="searchGuidance" class="insight-list">
                        <div class="insight-item">✓ 单个商品：点击商品卡片的 <strong>AI 处理</strong> 按钮</div>
                        <div class="insight-item">✓ 批量处理：勾选多个商品后点击 <strong>批量 AI 分类/描述</strong></div>
                    </div>
                </div>
            </div>
            <div id="salesStatus" class="status"></div>
            <div id="aiStatus" class="status"></div>
            <div id="salesMetrics" class="metrics"></div>
            <div id="salesResults"></div>
            <div id="aiResults" class="card" style="display:none; margin-top: 16px;">
                <div class="panel-header">
                    <div class="panel-copy">
                        <div class="panel-kicker">AI Processing Results</div>
                        <h3 class="panel-title">🤖 AI 处理结果</h3>
                    </div>
                    <div class="panel-meta">实时结果 · 立即查看</div>
                </div>
                <div id="aiResultsContent"></div>
            </div>
        </section>
        <section id="categories" class="tab-panel card">
            <div class="panel-header">
                <div class="panel-copy">
                    <div class="panel-kicker">Category Management</div>
                    <h2 class="panel-title">📂 商品分类</h2>
                    <p class="muted">查看近30天销售商品的分类情况，点击类别查看该类别下的所有商品。未分类商品将自动使用AI进行分类。</p>
                </div>
                <div class="panel-meta">分类浏览 · AI自动分类</div>
            </div>
            <div class="actions">
                <button class="btn" id="loadCategoriesButton">加载分类数据</button>
                <button class="btn secondary" id="autoClassifyButton">自动分类未分类商品</button>
            </div>
            <div id="categoryStatus" class="status"></div>
            <div id="categoryMetrics" class="metrics"></div>
            <div id="categoriesOverview"></div>
            <div id="categoryDetail" style="display:none; margin-top: 20px;">
                <div class="panel-header">
                    <div class="panel-copy">
                        <h3 class="panel-title" id="categoryDetailTitle">类别详情</h3>
                    </div>
                    <button class="btn secondary" id="backToCategoriesButton">返回分类列表</button>
                </div>
                <div id="categoryProducts"></div>
            </div>
        </section>
        <section id="batch" class="tab-panel card">
            <div class="panel-header">
                <div class="panel-copy">
                    <div class="panel-kicker">Batch Processing</div>
                    <h2 class="panel-title">⚙️ 批量处理</h2>
                    <p class="muted">批量执行 AI 分类或描述生成，适合处理大量相似商品。队列数据自动保存到本地存储。</p>
                </div>
                <div class="panel-meta">批量任务 · 进度跟踪</div>
            </div>
            <div id="batchProgress" style="display:none;">
                <div class="progress-bar"><div class="progress-fill" id="batchProgressFill" style="width: 0%;"></div></div>
                <div class="progress-text" id="batchProgressText">准备中...</div>
            </div>
            <div class="grid-2">
                <div class="detail-section">
                    <h3>创建批量任务</h3>
                    <div><label for="batchTaskType">任务类型</label><select id="batchTaskType"><option value="classify">批量 AI 分类</option><option value="describe">批量 AI 描述</option></select></div>
                    <div class="section-gap"><label for="batchLength">描述长度</label><select id="batchLength"><option value="short">简短</option><option value="medium" selected>中等</option><option value="long">详细</option></select></div>
                    <div class="actions"><button class="btn" id="runBatchButton">执行批量任务</button><button class="btn secondary" id="clearBatchButton">清空队列</button></div>
                    <div id="chartStatus" class="status">请先在销量查询中勾选商品加入批量队列。</div>
                </div>
                <div class="detail-section">
                    <h3>队列概览</h3>
                    <div id="summaryMetrics" class="metrics"></div>
                    <div class="muted-small">队列和结果库数据已自动保存到本地存储，刷新页面不会丢失。</div>
                </div>
            </div>
            <div id="chartResults"></div>
        </section>
        <section id="analytics" class="tab-panel card">
            <div class="panel-header">
                <div class="panel-copy">
                    <div class="panel-kicker">Analytics & Insights</div>
                    <h2 class="panel-title">📊 数据分析</h2>
                    <p class="muted">查看 AI 结果库、销售趋势分析和数据可视化，为运营决策提供参考依据。</p>
                </div>
                <div class="panel-meta">结果库 · 趋势 · 图表</div>
            </div>
            <div class="tabs" style="flex-direction: row; margin-bottom: 20px;">
                <button class="chip active" data-subtab="library">🗂️ AI 结果库</button>
                <button class="chip" data-subtab="trends">📈 趋势分析</button>
                <button class="chip" data-subtab="charts">📊 数据图表</button>
            </div>
            <div id="library-panel" class="subtab-panel">
                <div class="actions"><button class="btn" id="loadAlertsButton">刷新结果库</button><button class="btn secondary" id="exportLibraryButton">导出结果 JSON</button></div>
                <div id="alertMetrics" class="metrics"></div>
                <div id="alertStatus" class="status"></div>
                <div id="alertResults"></div>
            </div>
            <div id="trends-panel" class="subtab-panel" style="display:none;">
                <div class="grid-2">
                    <div><label for="trendQuery">商品关键词</label><input id="trendQuery" placeholder="输入商品关键词，留空则使用前 10 个商品"></div>
                    <div><label for="trendType">对比类型</label><select id="trendType"><option value="mom">月环比</option><option value="yoy">年同比</option></select></div>
                </div>
                <div class="grid-2 section-gap">
                    <div><label for="trendStartDate">开始日期</label><input id="trendStartDate" type="date"></div>
                    <div><label for="trendEndDate">结束日期</label><input id="trendEndDate" type="date"></div>
                </div>
                <div class="actions"><button class="btn" id="loadTrendButton">生成趋势分析</button></div>
                <div id="trendStatus" class="status"></div>
                <div id="trendMetrics" class="metrics"></div>
                <div id="trendResults"></div>
            </div>
            <div id="charts-panel" class="subtab-panel" style="display:none;">
                <p class="muted">基于最近一次搜索结果自动绘制图表。请先在销量查询中执行搜索。</p>
                <div class="grid-2"><div class="card"><canvas id="qtyChart"></canvas></div><div class="card"><canvas id="revenueChart"></canvas></div></div>
                <div class="status" id="chartVisStatus">请先在销量查询中完成一次搜索。</div>
            </div>
        </section>
        <section class="cards" style="margin-top: 30px;">
            <div class="card"><div class="label">待分类商品</div><div class="value" id="pendingClassifyCount">0</div></div>
            <div class="card"><div class="label">待描述商品</div><div class="value" id="pendingDescribeCount">0</div></div>
            <div class="card"><div class="label">批量队列</div><div class="value" id="batchTaskCount">0</div></div>
            <div class="card"><div class="label">AI 结果库</div><div class="value" id="aiLibraryCount">0</div></div>
        </section>
        </div>
    </main>
    <div class="footer">Copyright 2026 EasternMarket. All rights reserved.</div>
    <script>
        const tabs = document.querySelectorAll('.tab-button');
        const panels = document.querySelectorAll('.tab-panel');
        const brandLogo = document.getElementById('brandLogo');
        const brandLogoFallback = document.getElementById('brandLogoFallback');
        const STORAGE_KEYS = {
            BATCH_QUEUE: 'stockwise_batch_queue',
            AI_LIBRARY: 'stockwise_ai_library',
            BATCH_RESULTS: 'stockwise_batch_results',
        };

        function loadFromStorage(key, defaultValue = []) {
            try {
                const data = localStorage.getItem(key);
                return data ? JSON.parse(data) : defaultValue;
            } catch (e) {
                console.error('Failed to load from storage:', e);
                return defaultValue;
            }
        }

        function saveToStorage(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.error('Failed to save to storage:', e);
            }
        }

        const state = {
            lastQueryResults: [],
            selectedProducts: [],
            batchQueue: loadFromStorage(STORAGE_KEYS.BATCH_QUEUE, []),
            batchResults: loadFromStorage(STORAGE_KEYS.BATCH_RESULTS, []),
            aiLibrary: loadFromStorage(STORAGE_KEYS.AI_LIBRARY, []),
            currentProduct: null,
            lastSearchMeta: null,
        };
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
            
            if (button.dataset.tab === 'batch') {
                renderBatchCenter();
            }
            if (button.dataset.tab === 'analytics') {
                renderLibrary();
            }
        }));

        document.querySelectorAll('[data-subtab]').forEach(button => button.addEventListener('click', () => {
            const subtab = button.dataset.subtab;
            document.querySelectorAll('[data-subtab]').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            document.querySelectorAll('.subtab-panel').forEach(panel => panel.style.display = 'none');
            document.getElementById(`${subtab}-panel`).style.display = 'block';
        }));

        function setStatus(id, message, type='') {
            const el = document.getElementById(id);
            const normalizedType = type || (message ? 'info' : '');
            el.className = `status ${normalizedType}`;
            el.textContent = message || '';
        }

        function renderMetrics(id, items) {
            const container = document.getElementById(id);
            container.innerHTML = items.map(item => `<div class="metric"><div class="k">${item.label}</div><div class="v">${item.value}</div></div>`).join('');
        }

        function renderTable(containerId, rows) {
            const container = document.getElementById(containerId);
            if (!rows || !rows.length) {
                container.innerHTML = '<div class="empty-state"><strong>暂无可显示的数据</strong>请先执行查询或调整筛选条件。</div>';
                return;
            }
            const headers = Object.keys(rows[0]);
            container.innerHTML = `<table><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${headers.map(h => `<td>${row[h] ?? ''}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
        }

        async function requestJson(url, options) {
            const response = await fetch(url, options);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.message || '请求失败');
            }
            return data;
        }

        function openWorkspace(product) {
            // 在AI库中查找该产品的记录
            const classifyRecord = state.aiLibrary.find(item => 
                item.type === 'classify' && getProductKey(item.product) === getProductKey(product)
            );
            const describeRecord = state.aiLibrary.find(item => 
                item.type === 'describe' && getProductKey(item.product) === getProductKey(product)
            );
            
            // 切换到销量查询标签页
            switchTab('products');
            
            // 如果有分类结果，显示分类结果
            if (classifyRecord) {
                renderAiWorkspace('classify', classifyRecord.result);
            }
            // 如果有描述结果，显示描述结果
            else if (describeRecord) {
                renderAiWorkspace('describe', describeRecord.result);
            }
            // 如果都没有，显示提示
            else {
                const container = document.getElementById('aiResults');
                const content = document.getElementById('aiResultsContent');
                if (container && content) {
                    content.innerHTML = '<div class="empty-state"><strong>未找到AI处理结果</strong>请先对该商品执行AI分类或描述。</div>';
                    container.style.display = 'block';
                }
            }
        }

        function switchTab(tabId) {
            tabs.forEach(tab => tab.classList.toggle('active', tab.dataset.tab === tabId));
            panels.forEach(panel => panel.classList.toggle('active', panel.id === tabId));
            if (tabId === 'batch') renderBatchCenter();
            if (tabId === 'analytics') renderLibrary();
        }

        function toId(value) {
            return String(value || '').trim().toLowerCase();
        }

        function getProductKey(product) {
            return [product['商品信息'], product['SKU'], product['Product Code']].map(toId).join('|');
        }

        function isSelected(product) {
            const key = getProductKey(product);
            return state.selectedProducts.some(item => getProductKey(item) === key);
        }

        function hasLibraryRecord(product, type) {
            const key = getProductKey(product);
            return state.aiLibrary.some(item => item.type === type && item.key === key);
        }

        function matchesSearchMode(product, query, mode) {
            const keyword = toId(query);
            if (!keyword) return true;
            const name = toId(product['商品信息']);
            const sku = toId(product['SKU']);
            const code = toId(product['Product Code']);
            if (mode === 'name') return name.includes(keyword);
            if (mode === 'sku') return sku.includes(keyword);
            if (mode === 'code') return code.includes(keyword);
            return name.includes(keyword) || sku.includes(keyword) || code.includes(keyword);
        }

        function matchesStatusFilter(product, status) {
            const classified = hasLibraryRecord(product, 'classify');
            const described = hasLibraryRecord(product, 'describe');
            if (status === 'pending_classify') return !classified;
            if (status === 'pending_describe') return !described;
            if (status === 'completed') return classified && described;
            return true;
        }

        function getVisibleSearchResults() {
            const query = document.getElementById('query').value.trim();
            const mode = document.getElementById('searchMode').value;
            const status = document.getElementById('statusFilter').value;
            return state.lastQueryResults.filter(item => matchesSearchMode(item, query, mode) && matchesStatusFilter(item, status));
        }

        function syncOverview() {
            const pendingClassify = state.lastQueryResults.filter(item => !hasLibraryRecord(item, 'classify')).length;
            const pendingDescribe = state.lastQueryResults.filter(item => !hasLibraryRecord(item, 'describe')).length;
            document.getElementById('pendingClassifyCount').textContent = pendingClassify;
            document.getElementById('pendingDescribeCount').textContent = pendingDescribe;
            document.getElementById('batchTaskCount').textContent = state.batchQueue.length;
            document.getElementById('aiLibraryCount').textContent = state.aiLibrary.length;
        }

        function buildProductPayload(product) {
            return {
                name: product['商品信息'],
                sku: product['SKU'] === '-' ? '' : product['SKU'],
                code: product['Product Code'] === '-' ? '' : product['Product Code'],
                price: Number(String(product['售价']).replace('$', '')) || 0,
            };
        }

        async function showAiDialog(product) {
            const classified = hasLibraryRecord(product, 'classify');
            const described = hasLibraryRecord(product, 'describe');
            const actions = [];
            if (!classified) actions.push('AI 分类');
            if (!described) actions.push('AI 描述');
            if (actions.length === 0) {
                setStatus('salesStatus', '该商品已完成 AI 分类和描述。', 'info');
                return;
            }
            const action = actions.length === 1 ? actions[0] : await promptUserChoice(actions);
            if (action === 'AI 分类') {
                await runAiTask('classify', buildProductPayload(product));
            } else if (action === 'AI 描述') {
                await runAiTask('describe', buildProductPayload(product));
            }
            renderSearchResults(getVisibleSearchResults());
        }

        async function promptUserChoice(actions) {
            return actions[0];
        }

        async function batchProcessSelected(type) {
            if (state.selectedProducts.length === 0) {
                setStatus('salesStatus', '请先勾选商品。', 'error');
                return;
            }
            const total = state.selectedProducts.length;
            let success = 0;
            let failed = 0;
            setStatus('salesStatus', `正在批量处理 ${total} 个商品...`, 'info');
            for (let i = 0; i < state.selectedProducts.length; i++) {
                const product = state.selectedProducts[i];
                state.currentProduct = product;
                setStatus('salesStatus', `正在处理 ${i + 1}/${total}: ${product['商品信息']}`, 'info');
                const result = await runAiTask(type, buildProductPayload(product));
                if (result) success++; else failed++;
            }
            setStatus('salesStatus', `批量处理完成：成功 ${success} 个，失败 ${failed} 个。`, failed > 0 ? 'error' : 'success');
            state.selectedProducts = [];
            renderSearchResults(getVisibleSearchResults());
            syncOverview();
        }

        function renderSearchResults(rows) {
            const container = document.getElementById('salesResults');
            if (!rows || !rows.length) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📦</div><strong>没有匹配到商品</strong>可以尝试更换关键词，或调整时间范围与筛选条件。</div>';
                return;
            }
            const selectedCount = state.selectedProducts.length;
            container.innerHTML = `
                <div class="inline-actions section-gap-sm">
                    <button class="chip" id="selectAllResults">全选 (${rows.length})</button>
                    ${selectedCount > 0 ? `
                        <button class="chip active" id="batchClassifySelected">批量 AI 分类 (${selectedCount})</button>
                        <button class="chip active" id="batchDescribeSelected">批量 AI 描述 (${selectedCount})</button>
                        <button class="chip" id="addToQueue">加入批量队列 (${selectedCount})</button>
                    ` : ''}
                </div>
                <div class="product-list">
                    ${rows.map((row, index) => {
                        const selected = isSelected(row);
                        const classified = hasLibraryRecord(row, 'classify');
                        const described = hasLibraryRecord(row, 'describe');
                        return `
                            <div class="product-item">
                                <div class="product-top">
                                    <div class="product-main">
                                        <div class="selection-box"><input type="checkbox" class="result-selector" data-index="${index}" ${selected ? 'checked' : ''}><h3 class="product-title">${row['商品信息']}</h3></div>
                                        <div class="meta">SKU: ${row['SKU']} · Code: ${row['Product Code']} · 售价: ${row['售价']}</div>
                                        <div class="meta">区间销量: ${row['区间销量']} · 销售额: ${row['销售总额']}</div>
                                        <div class="status-badges">
                                            <span class="badge ${classified ? 'success' : 'warn'}">${classified ? '✓ 已分类' : '待分类'}</span>
                                            <span class="badge ${described ? 'success' : 'warn'}">${described ? '✓ 已描述' : '待描述'}</span>
                                        </div>
                                    </div>
                                    <div class="product-actions">
                                        <button class="btn ai-process" data-index="${index}">AI 处理</button>
                                        <button class="btn-icon more-actions" data-index="${index}">⋮</button>
                                        <div class="dropdown-menu" id="dropdown-${index}">
                                            <div class="dropdown-item quick-classify" data-index="${index}">AI 分类</div>
                                            <div class="dropdown-item quick-describe" data-index="${index}">AI 描述</div>
                                            <div class="dropdown-item queue-single" data-index="${index}">加入批量队列</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;

            document.getElementById('selectAllResults').onclick = () => {
                state.selectedProducts = [...rows];
                renderSearchResults(getVisibleSearchResults());
                syncOverview();
            };
            if (selectedCount > 0) {
                document.getElementById('batchClassifySelected').onclick = async () => {
                    await batchProcessSelected('classify');
                };
                document.getElementById('batchDescribeSelected').onclick = async () => {
                    await batchProcessSelected('describe');
                };
                document.getElementById('addToQueue').onclick = () => {
                    addProductsToBatch(state.selectedProducts);
                    setStatus('salesStatus', `已将 ${selectedCount} 个商品加入批量队列。`, 'success');
                    renderSearchResults(getVisibleSearchResults());
                };
            }
            container.querySelectorAll('.result-selector').forEach(el => el.onchange = () => {
                toggleSelection(rows[Number(el.dataset.index)]);
            });
            container.querySelectorAll('.ai-process').forEach(el => el.onclick = async () => {
                const product = rows[Number(el.dataset.index)];
                state.currentProduct = product;
                await showAiDialog(product);
            });
            container.querySelectorAll('.more-actions').forEach(el => el.onclick = (e) => {
                e.stopPropagation();
                const dropdown = document.getElementById(`dropdown-${el.dataset.index}`);
                document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.remove('show'));
                dropdown.classList.toggle('show');
            });
            container.querySelectorAll('.quick-classify').forEach(el => el.onclick = async () => {
                const product = rows[Number(el.dataset.index)];
                state.currentProduct = product;
                await runAiTask('classify', buildProductPayload(product));
                renderSearchResults(getVisibleSearchResults());
            });
            container.querySelectorAll('.quick-describe').forEach(el => el.onclick = async () => {
                const product = rows[Number(el.dataset.index)];
                state.currentProduct = product;
                await runAiTask('describe', buildProductPayload(product));
                renderSearchResults(getVisibleSearchResults());
            });
            container.querySelectorAll('.queue-single').forEach(el => el.onclick = () => {
                addProductsToBatch([rows[Number(el.dataset.index)]]); 
                renderSearchResults(getVisibleSearchResults());
            });
            document.addEventListener('click', () => {
                document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.remove('show'));
            });
        }

        function toggleSelection(product) {
            const key = getProductKey(product);
            if (state.selectedProducts.some(item => getProductKey(item) === key)) {
                state.selectedProducts = state.selectedProducts.filter(item => getProductKey(item) !== key);
            } else {
                state.selectedProducts.push(product);
            }
            renderSearchResults(getVisibleSearchResults());
            syncOverview();
        }


        function addLibraryRecord(type, product, payload) {
            const key = getProductKey(product);
            state.aiLibrary = state.aiLibrary.filter(item => !(item.type === type && item.key === key));
            state.aiLibrary.unshift({
                type,
                key,
                product: JSON.parse(JSON.stringify(product)),
                result: payload,
                createdAt: new Date().toISOString(),
            });
            saveToStorage(STORAGE_KEYS.AI_LIBRARY, state.aiLibrary);
        }

        function renderAiWorkspace(type, data) {
            const container = document.getElementById('aiResults');
            const content = document.getElementById('aiResultsContent');
            
            if (!container || !content) return;
            
            if (type === 'classify') {
                content.innerHTML = `
                    <div class="detail-grid">
                        <div class="detail-section">
                            <h3>📊 分类结果</h3>
                            <div class="detail-row">
                                <div class="detail-key">主类别</div>
                                <div class="detail-value">${data.main_category || '未分类'}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-key">子类别</div>
                                <div class="detail-value">${data.sub_category || '未分类'}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-key">置信度</div>
                                <div class="detail-value">${Math.round((data.confidence_score || 0) * 100)}%</div>
                            </div>
                        </div>
                        <div class="detail-section">
                            <h3>🏷️ 属性标签</h3>
                            <div class="detail-block">
                                ${formatTagList(data.attributes)}
                            </div>
                            <div class="detail-row section-gap-sm">
                                <div class="detail-key">目标客户</div>
                                <div class="detail-value-text">${formatTagList(data.target_customers)}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-key">存储要求</div>
                                <div class="detail-value-text">${data.storage_requirements || '无特殊要求'}</div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (type === 'describe') {
                content.innerHTML = `
                    <div class="detail-grid">
                        <div class="detail-section">
                            <h3>📝 商品描述</h3>
                            <div class="detail-value-text">${data.description || '暂无描述'}</div>
                            <div class="detail-row section-gap-sm">
                                <div class="detail-key">置信度</div>
                                <div class="detail-value">${Math.round((data.confidence_score || 0) * 100)}%</div>
                            </div>
                        </div>
                        <div class="detail-section">
                            <h3>🔍 营销信息</h3>
                            <div class="detail-row">
                                <div class="detail-key">关键词</div>
                                <div class="detail-value-text">${formatTagList(data.keywords)}</div>
                            </div>
                            <div class="detail-row section-gap-sm">
                                <div class="detail-key">卖点</div>
                                <div class="detail-value-text">${formatTagList(data.selling_points)}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-key">使用建议</div>
                                <div class="detail-value-text">${data.usage_suggestions || '暂无建议'}</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // 显示AI结果区域
            container.style.display = 'block';
            // 滚动到结果区域
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function formatTagList(items) {
            if (!items || !items.length) return '<span class="muted-small">暂无</span>';
            return `<div class="tag-list">${items.map(item => `<span class="badge">${item}</span>`).join('')}</div>`;
        }


        function addProductsToBatch(products) {
            products.forEach(product => {
                const key = getProductKey(product);
                if (!state.batchQueue.some(item => getProductKey(item) === key)) {
                    state.batchQueue.push(product);
                }
            });
            saveToStorage(STORAGE_KEYS.BATCH_QUEUE, state.batchQueue);
            renderBatchCenter();
            syncOverview();
        }

        function renderBatchCenter() {
            renderMetrics('summaryMetrics', [
                { label: '待处理商品', value: state.batchQueue.length },
                { label: '已完成任务', value: state.batchResults.length },
                { label: '分类结果', value: state.aiLibrary.filter(item => item.type === 'classify').length },
                { label: '描述结果', value: state.aiLibrary.filter(item => item.type === 'describe').length },
            ]);
            const container = document.getElementById('chartResults');
            const queueHtml = state.batchQueue.length ? `
                <div class="detail-section section-gap">
                    <h3>当前队列 (${state.batchQueue.length} 个商品)</h3>
                    <div class="batch-list">${state.batchQueue.map((item, index) => `<div class="batch-item"><strong>${item['商品信息']}</strong><div class="muted-small">SKU: ${item['SKU']} · Code: ${item['Product Code']}</div><div class="inline-actions section-gap-sm"><button class="chip batch-remove" data-index="${index}">移除</button></div></div>`).join('')}</div>
                  <div class="empty-state"><div class="empty-state-icon">⚙️</div><strong>批量队列为空</strong>请在销量查询中勾选商品后加入队列。</div>';
            const resultHtml = state.batchResults.length ? `
                <div class="detail-section section-gap">
                    <h3>最近批量任务</h3>
                    <div class="batch-list">${state.batchResults.map(item => `<div class="batch-item"><strong>${item.label}</strong><div class="muted-small">${item.createdAt}</div><div class="muted-small">成功 ${item.success} 个，失败 ${item.failed} 个</div></div>`).join('')}</div>
                </div>` : '';
            container.innerHTML = queueHtml + resultHtml;
            container.querySelectorAll('.batch-remove').forEach(el => el.onclick = () => {
                state.batchQueue.splice(Number(el.dataset.index), 1);
                saveToStorage(STORAGE_KEYS.BATCH_QUEUE, state.batchQueue);
                renderBatchCenter();
                syncOverview();
            });
        }

        function renderLibrary() {
            renderMetrics('alertMetrics', [
                { label: '全部记录', value: state.aiLibrary.length },
                { label: '分类记录', value: state.aiLibrary.filter(item => item.type === 'classify').length },
                { label: '描述记录', value: state.aiLibrary.filter(item => item.type === 'describe').length },
                { label: '本地存储', value: state.aiLibrary.length > 0 ? '已启用' : '空' },
            ]);
            const container = document.getElementById('alertResults');
            if (!state.aiLibrary.length) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🗂️</div><strong>结果库暂时为空</strong>在销量查询中执行 AI 分类或描述，结果会自动保存到这里。</div>';
                setStatus('alertStatus', '当前还没有结果记录。');
                return;
            }
            container.innerHTML = `<div class="library-list">${state.aiLibrary.map((item, index) => `
                <div class="library-item">
                    <div class="product-top">
                        <div>
                            <strong>${item.product['商品信息']}</strong>
                            <div class="meta">${item.type === 'classify' ? '分类结果' : '描述结果'} · ${item.createdAt}</div>
                        </div>
                        <div class="inline-actions"><button class="chip library-open" data-index="${index}">查看</button></div>
                    </div>
                </div>`).join('')}</div>`;
            container.querySelectorAll('.library-open').forEach(el => el.onclick = () => {
                const record = state.aiLibrary[Number(el.dataset.index)];
                openWorkspace(record.product);
            });
            // 移除有问题的复制JSON功能 - record.payload字段不存在导致返回undefined
            setStatus('alertStatus', `已载入 ${state.aiLibrary.length} 条结果记录。`, 'success');
        }

        function drawCharts(rows) {
            const labels = rows.map(row => row['商品信息']);
            const qtyData = rows.map(row => Number(row['区间销量']) || 0);
            const revenueData = rows.map(row => Number(String(row['销售总额']).replace('$', '').replace(/,/g,'')) || 0);
            if (qtyChart) qtyChart.destroy();
            if (revenueChart) revenueChart.destroy();
            qtyChart = new Chart(document.getElementById('qtyChart'), { type: 'bar', data: { labels, datasets: [{ label: '销量', data: qtyData, backgroundColor: '#1e63d2' }] }, options: { responsive: true, plugins: { legend: { display: false } } } });
            revenueChart = new Chart(document.getElementById('revenueChart'), { type: 'doughnut', data: { labels, datasets: [{ label: '销售额', data: revenueData, backgroundColor: ['#1e63d2','#4f8df0','#7aacff','#99bfff','#bfd7ff','#dce9ff'] }] }, options: { responsive: true } });
            setStatus('chartVisStatus', `已根据最近查询结果绘制 ${rows.length} 个商品的图表。`, 'success');
        }

        // 添加自动加载30天数据的功能
        async function load30DaysChartData() {
            setStatus('chartStatus', '正在加载近 30 天数据...', 'info');
            try {
                const data = await requestJson('/api/charts/30days');
                if (!data.products || !data.products.length) {
                    setStatus('chartStatus', data.message || '近 30 天没有可显示的销售记录。', 'error');
                    return;
                }
                
                // 绘制前10名占比饼图
                drawTop10PieChart(data.products);
                
                // 显示完整数据表格
                renderFullProductsTable(data.products);
                
                // 显示数据概览
                renderSummaryMetrics(data);
                
                setStatus('chartStatus', `已加载近 30 天数据，共 ${data.total_products} 个商品。`, 'success');
            } catch (error) {
                setStatus('chartStatus', error.message, 'error');
            }
        }

        function drawTop10PieChart(products) {
            // 获取前10名
            const top10 = products.slice(0, 10);
            const others = products.slice(10);
            
            // 计算其他商品总额
            const othersRevenue = others.reduce((sum, p) => sum + parseFloat(p['销售总额'].replace('$', '').replace(',', '')), 0);
            
            // 准备图表数据
            const chartData = [
                ...top10.map(p => ({
                    name: p['商品信息'],
                    value: parseFloat(p['销售总额'].replace('$', '').replace(',', ''))
                }))
            ];
            
            // 如果有其他商品，添加到图表
            if (othersRevenue > 0) {
                chartData.push({
                    name: '其他',
                    value: othersRevenue
                });
            }
            
            // 销毁旧图表
            if (revenueChart) revenueChart.destroy();
            
            // 创建新的饼图
            const ctx = document.getElementById('revenueChart').getContext('2d');
            revenueChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: chartData.map(d => d.name),
                    datasets: [{
                        data: chartData.map(d => d.value),
                        backgroundColor: [
                            '#1e63d2', '#4f8df0', '#7aacff', '#99bfff', '#bfd7ff', '#dce9ff',
                            '#e8f4ff', '#f0f7ff', '#f8fbff', '#ffffff', '#e0e0e0'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                padding: 15,
                                font: { size: 12 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = '$' + context.parsed.toFixed(2);
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return `${context.label}: ${value} (${percentage}%)`;
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: '过去30天销售金额占比 (前10名 + 其他)',
                            font: { size: 16 }
                        }
                    }
                }
            });
        }

        function renderFullProductsTable(products) {
            const container = document.getElementById('chartResults');
            if (!products || !products.length) {
                container.innerHTML = '<p class="muted">暂无数据。</p>';
                return;
            }
            
            // 创建表格HTML
            let tableHTML = `
                <div style="margin-top: 30px;">
                    <h3 style="margin-bottom: 15px;">过去30天全部销售商品明细</h3>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; background: #fff; border-radius: 14px; overflow: hidden;">
                            <thead>
                                <tr style="background: #f7faff;">
                                    <th style="padding: 12px; text-align: left; font-size: 14px;">商品信息</th>
                                    <th style="padding: 12px; text-align: left; font-size: 14px;">售价</th>
                                    <th style="padding: 12px; text-align: left; font-size: 14px;">销量</th>
                                    <th style="padding: 12px; text-align: left; font-size: 14px;">销售总额</th>
                                    <th style="padding: 12px; text-align: left; font-size: 14px;">Product Code</th>
                                    <th style="padding: 12px; text-align: left; font-size: 14px;">SKU</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            products.forEach((product, index) => {
                const rowStyle = index % 2 === 0 ? 'background: #fff;' : 'background: #f8fbff;';
                tableHTML += `
                    <tr style="${rowStyle} border-bottom: 1px solid #edf2fa;">
                        <td style="padding: 12px; font-size: 14px;">${product['商品信息']}</td>
                        <td style="padding: 12px; font-size: 14px;">${product['售价']}</td>
                        <td style="padding: 12px; font-size: 14px;">${product['区间销量']}</td>
                        <td style="padding: 12px; font-size: 14px; font-weight: bold;">${product['销售总额']}</td>
                        <td style="padding: 12px; font-size: 14px;">${product['Product Code']}</td>
                        <td style="padding: 12px; font-size: 14px;">${product['SKU']}</td>
                    </tr>
                `;
            });
            
            tableHTML += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            container.innerHTML = tableHTML;
        }

        function renderSummaryMetrics(data) {
            const container = document.getElementById('summaryMetrics');
            const top10Revenue = data.products.slice(0, 10).reduce((sum, p) => sum + parseFloat(p['销售总额'].replace('$', '').replace(',', '')), 0);
            const top10Percentage = ((top10Revenue / data.total_revenue) * 100).toFixed(1);
            
            container.innerHTML = [
                { label: '总商品数', value: data.total_products },
                { label: '总销售额', value: '$' + data.total_revenue.toFixed(2) },
                { label: '前10名销售额', value: '$' + top10Revenue.toFixed(2) },
                { label: '前10名占比', value: top10Percentage + '%' }
            ].map(item => `<div class="metric"><div class="k">${item.label}</div><div class="v">${item.value}</div></div>`).join('');
        }

        document.getElementById('searchButton').addEventListener('click', async () => {
            const query = document.getElementById('query').value.trim();
            const startDate = document.getElementById('start_date').value;
            const endDate = document.getElementById('end_date').value;
            if (!query) { setStatus('salesStatus', '请输入搜索关键词。', 'error'); return; }
            setStatus('salesStatus', '正在查询商品数据...', 'info');
            try {
                const data = await requestJson(`/api/sales/search?query=${encodeURIComponent(query)}&start_date=${startDate}&end_date=${endDate}`);
                state.lastQueryResults = data.results || [];
                renderMetrics('salesMetrics', [
                    { label: '匹配商品', value: data.matched_products },
                    { label: '销售记录', value: data.sales_records },
                    { label: '总销量', value: data.summary.total_quantity },
                    { label: '总销售额', value: '$' + Number(data.summary.total_revenue || 0).toFixed(2) },
                ]);
                state.lastSearchMeta = data;
                renderSearchResults(getVisibleSearchResults());
                setStatus('salesStatus', `查询完成：${data.period}`, 'success');
                syncOverview();
            } catch (error) {
                renderMetrics('salesMetrics', []);
                renderSearchResults([]);
                setStatus('salesStatus', error.message, 'error');
            }
        });

        document.getElementById('exportButton').addEventListener('click', async () => {
            setStatus('salesStatus', '正在准备导出数据...', 'info');
            try {
                const data = await requestJson('/api/sales/export');
                const rows = data.data || [];
                if (!rows.length) { setStatus('salesStatus', '近 30 天没有销售记录。', 'error'); return; }
                const headers = Object.keys(rows[0]);
                const csv = [headers.join(','), ...rows.map(row => headers.map(h => `"${String(row[h] ?? '').replaceAll('"','""')}"`).join(','))].join('\n');
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

        document.getElementById('loadAlertsButton').addEventListener('click', async () => renderLibrary());

        document.getElementById('loadTrendButton').addEventListener('click', async () => {
            const query = document.getElementById('trendQuery').value.trim();
            const period = document.getElementById('trendType').value;
            const startDate = document.getElementById('trendStartDate').value;
            const endDate = document.getElementById('trendEndDate').value;
            setStatus('trendStatus', '正在生成趋势分析...', 'info');
            try {
                const params = new URLSearchParams({ period, start_date: startDate, end_date: endDate });
                if (query) params.set('query', query);
                const data = await requestJson(`/api/trends/analysis?${params.toString()}`);
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
                setStatus('trendStatus', `趋势分析已完成：${data.comparison_type === 'mom' ? '月环比' : '年同比'}`, 'success');
            } catch (error) {
                setStatus('trendStatus', error.message, 'error');
            }
        });


        async function runAiTask(type, customPayload) {
            const payload = customPayload || buildAiPayload();
            if (!payload.name) { setStatus('aiStatus', '请输入商品名称。', 'error'); return null; }
            const endpoint = type === 'classify' ? '/api/ai/classify' : '/api/ai/describe';
            const statusText = type === 'classify' ? '正在生成 AI 分类结果...' : '正在生成 AI 描述...';
            setStatus('aiStatus', statusText, 'info');
            try {
                const data = await requestJson(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                if (state.currentProduct) addLibraryRecord(type, state.currentProduct, data);
                renderAiWorkspace(type, data);
                setStatus('aiStatus', type === 'classify' ? 'AI 分类已完成。' : 'AI 描述已生成。', 'success');
                return data;
            } catch (error) {
                setStatus('aiStatus', error.message, 'error');
                return null;
            }
        }


        document.getElementById('runBatchButton').addEventListener('click', async () => {
            if (!state.batchQueue.length) {
                setStatus('chartStatus', '批量队列为空，请先添加商品。', 'error');
                return;
            }
            const taskType = document.getElementById('batchTaskType').value;
            const length = document.getElementById('batchLength').value;
            const total = state.batchQueue.length;
            let success = 0;
            let failed = 0;
            
            document.getElementById('batchProgress').style.display = 'block';
            
            for (let i = 0; i < state.batchQueue.length; i++) {
                const product = state.batchQueue[i];
                state.currentProduct = product;
                
                const progress = Math.round(((i + 1) / total) * 100);
                document.getElementById('batchProgressFill').style.width = `${progress}%`;
                document.getElementById('batchProgressText').textContent = `正在处理 ${i + 1}/${total}: ${product['商品信息']}`;
                
                const payload = {
                    name: product['商品信息'],
                    sku: product['SKU'] === '-' ? '' : product['SKU'],
                    code: product['Product Code'] === '-' ? '' : product['Product Code'],
                    price: Number(String(product['售价']).replace('$', '')) || 0,
                };
                if (taskType === 'describe') payload.target_length = length;
                const result = await runAiTask(taskType, payload);
                if (result) success += 1; else failed += 1;
            }
            
            document.getElementById('batchProgress').style.display = 'none';
            
            state.batchResults.unshift({
                label: taskType === 'classify' ? '批量 AI 分类' : '批量 AI 描述',
                createdAt: new Date().toLocaleString(),
                success,
                failed,
            });
            saveToStorage(STORAGE_KEYS.BATCH_RESULTS, state.batchResults);
            setStatus('chartStatus', `批量任务完成：成功 ${success} 个，失败 ${failed} 个。`, failed ? 'error' : 'success');
            renderBatchCenter();
            syncOverview();
        });

        document.getElementById('clearBatchButton').addEventListener('click', () => {
            if (!confirm(`确定要清空批量队列吗？这将移除 ${state.batchQueue.length} 个商品。`)) return;
            state.batchQueue = [];
            saveToStorage(STORAGE_KEYS.BATCH_QUEUE, state.batchQueue);
            renderBatchCenter();
            syncOverview();
            setStatus('chartStatus', '批量队列已清空。', 'success');
        });

        document.getElementById('exportLibraryButton').addEventListener('click', () => {
            const blob = new Blob([JSON.stringify(state.aiLibrary, null, 2)], { type: 'application/json;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'stockwise_ai_library.json';
            link.click();
            setStatus('alertStatus', '结果库已导出。', 'success');
        });

        // Category Management Functions
        let categoryData = {
            products: [],
            categories: {},
            unclassified: []
        };

        async function loadCategories() {
            setStatus('categoryStatus', '正在加载近30天销售商品数据...', 'info');
            try {
                const data = await requestJson('/api/categories/overview');
                categoryData.products = data.products || [];
                
                // 分析分类情况
                analyzeCategoryData();
                renderCategoryOverview();
                
                setStatus('categoryStatus', `已加载 ${categoryData.products.length} 个商品，${categoryData.unclassified.length} 个待分类`, 'success');
            } catch (error) {
                setStatus('categoryStatus', error.message, 'error');
            }
        }

        function analyzeCategoryData() {
            categoryData.categories = {};
            categoryData.unclassified = [];
            
            categoryData.products.forEach(product => {
                const key = getProductKey(product);
                const classifyRecord = state.aiLibrary.find(item => 
                    item.type === 'classify' && item.key === key
                );
                
                if (classifyRecord && classifyRecord.result) {
                    const mainCategory = classifyRecord.result.main_category || '未分类';
                    if (!categoryData.categories[mainCategory]) {
                        categoryData.categories[mainCategory] = [];
                    }
                    categoryData.categories[mainCategory].push({
                        ...product,
                        classification: classifyRecord.result
                    });
                } else {
                    categoryData.unclassified.push(product);
                }
            });
        }

        function renderCategoryOverview() {
            const container = document.getElementById('categoriesOverview');
            const categories = Object.keys(categoryData.categories).sort();
            
            renderMetrics('categoryMetrics', [
                { label: '总商品数', value: categoryData.products.length },
                { label: '已分类', value: categoryData.products.length - categoryData.unclassified.length },
                { label: '待分类', value: categoryData.unclassified.length },
                { label: '类别数', value: categories.length }
            ]);
            
            if (categories.length === 0 && categoryData.unclassified.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📂</div><strong>暂无数据</strong>请先点击"加载分类数据"按钮。</div>';
                return;
            }
            
            let html = '';
            
            // 显示已分类的类别
            if (categories.length > 0) {
                html += '<div style="margin-bottom: 20px;"><h3>商品分类</h3><div class="grid-3">';
                categories.forEach(category => {
                    const count = categoryData.categories[category].length;
                    const totalRevenue = categoryData.categories[category].reduce((sum, p) => {
                        const revenue = parseFloat(String(p['销售总额'] || '0').replace('$', '').replace(',', ''));
                        return sum + revenue;
                    }, 0);
                    
                    html += `
                        <div class="card" style="cursor: pointer; transition: all 0.2s;" onclick="showCategoryDetail('${category}')">
                            <div class="label">${category}</div>
                            <div class="value">${count} 个商品</div>
                            <div class="meta" style="margin-top: 8px;">销售额: $${totalRevenue.toFixed(2)}</div>
                        </div>
                    `;
                });
                html += '</div></div>';
            }
            
            // 显示未分类商品
            if (categoryData.unclassified.length > 0) {
                html += `
                    <div class="detail-section" style="margin-top: 20px;">
                        <h3>未分类商品 (${categoryData.unclassified.length})</h3>
                        <p class="muted-small">以下商品尚未进行AI分类，点击"自动分类未分类商品"按钮进行批量分类。</p>
                        <div class="product-list" style="margin-top: 12px;">
                            ${categoryData.unclassified.slice(0, 10).map(product => `
                                <div class="product-item">
                                    <strong>${product['商品信息']}</strong>
                                    <div class="meta">SKU: ${product['SKU']} · 销量: ${product['区间销量']} · 销售额: ${product['销售总额']}</div>
                                </div>
                            `).join('')}
                            ${categoryData.unclassified.length > 10 ? `<div class="muted-small" style="margin-top: 10px;">还有 ${categoryData.unclassified.length - 10} 个商品未显示...</div>` : ''}
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }

        function showCategoryDetail(categoryName) {
            const products = categoryData.categories[categoryName] || [];
            document.getElementById('categoryDetailTitle').textContent = `${categoryName} (${products.length} 个商品)`;
            
            const container = document.getElementById('categoryProducts');
            container.innerHTML = `
                <div class="product-list">
                    ${products.map(product => {
                        const classification = product.classification || {};
                        return `
                            <div class="product-item">
                                <div class="product-top">
                                    <div class="product-main">
                                        <h3 class="product-title">${product['商品信息']}</h3>
                                        <div class="meta">SKU: ${product['SKU']} · Code: ${product['Product Code']} · 售价: ${product['售价']}</div>
                                        <div class="meta">销量: ${product['区间销量']} · 销售额: ${product['销售总额']}</div>
                                        <div class="status-badges" style="margin-top: 10px;">
                                            <span class="badge success">主类别: ${classification.main_category || '-'}</span>
                                            <span class="badge">子类别: ${classification.sub_category || '-'}</span>
                                            ${classification.confidence_score ? `<span class="badge">置信度: ${Math.round(classification.confidence_score * 100)}%</span>` : ''}
                                        </div>
                                        ${classification.attributes && classification.attributes.length > 0 ? `
                                            <div style="margin-top: 8px;">
                                                <div class="muted-small">属性标签:</div>
                                                <div class="tag-list">${classification.attributes.map(attr => `<span class="badge">${attr}</span>`).join('')}</div>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
            
            document.getElementById('categoriesOverview').style.display = 'none';
            document.getElementById('categoryDetail').style.display = 'block';
        }

        async function autoClassifyUnclassified() {
            if (categoryData.unclassified.length === 0) {
                setStatus('categoryStatus', '没有待分类的商品。', 'info');
                return;
            }
            
            const confirmed = confirm(`将对 ${categoryData.unclassified.length} 个商品进行AI自动分类，这可能需要一些时间。是否继续？`);
            if (!confirmed) return;
            
            setStatus('categoryStatus', `正在分类 ${categoryData.unclassified.length} 个商品...`, 'info');
            
            try {
                const data = await requestJson('/api/categories/batch-classify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ products: categoryData.unclassified })
                });
                
                // 保存分类结果到AI库
                data.results.forEach(result => {
                    if (result.success && result.classification) {
                        const product = result.product;
                        const key = getProductKey(product);
                        state.aiLibrary = state.aiLibrary.filter(item => !(item.type === 'classify' && item.key === key));
                        state.aiLibrary.unshift({
                            type: 'classify',
                            key,
                            product: JSON.parse(JSON.stringify(product)),
                            result: result.classification,
                            createdAt: new Date().toISOString(),
                        });
                    }
                });
                
                saveToStorage(STORAGE_KEYS.AI_LIBRARY, state.aiLibrary);
                
                setStatus('categoryStatus', `分类完成：成功 ${data.success_count} 个，失败 ${data.failed_count} 个`, data.failed_count > 0 ? 'error' : 'success');
                
                // 重新加载分类数据
                analyzeCategoryData();
                renderCategoryOverview();
                syncOverview();
            } catch (error) {
                setStatus('categoryStatus', error.message, 'error');
            }
        }

        document.getElementById('loadCategoriesButton').addEventListener('click', loadCategories);
        document.getElementById('autoClassifyButton').addEventListener('click', autoClassifyUnclassified);
        document.getElementById('backToCategoriesButton').addEventListener('click', () => {
            document.getElementById('categoriesOverview').style.display = 'block';
            document.getElementById('categoryDetail').style.display = 'none';
        });

        window.showCategoryDetail = showCategoryDetail;


        document.querySelectorAll('.quick-filters .chip').forEach(chip => chip.addEventListener('click', () => {
            document.querySelectorAll('.quick-filters .chip').forEach(item => item.classList.remove('active'));
            chip.classList.add('active');
            const days = Number(chip.dataset.days || 30);
            const today = new Date();
            const start = new Date();
            start.setDate(today.getDate() - days);
            const fmt = (date) => date.toISOString().slice(0, 10);
            document.getElementById('start_date').value = fmt(start);
            document.getElementById('end_date').value = fmt(today);
        }));

        document.getElementById('query').addEventListener('keydown', event => {
            if (event.key === 'Enter') document.getElementById('searchButton').click();
        });

        document.getElementById('searchMode').addEventListener('change', () => {
            renderSearchResults(getVisibleSearchResults());
        });

        document.getElementById('statusFilter').addEventListener('change', () => {
            renderSearchResults(getVisibleSearchResults());
        });

        requestJson('/health').then(data => {
            const availability = data.features?.ai_enabled ? `已启用 (${data.features.ai_provider})` : '未配置';
            document.getElementById('aiAvailability').textContent = availability;
        }).catch(() => {
            document.getElementById('aiAvailability').textContent = '状态未知';
        });

        setDefaultDates();
        renderBatchCenter();
        renderLibrary();
        syncOverview();
        
        console.log('StockWise initialized');
        console.log('Batch Queue:', state.batchQueue.length, 'items');
        console.log('AI Library:', state.aiLibrary.length, 'records');
        console.log('Batch Results:', state.batchResults.length, 'tasks');
    </script>
</body>
</html>'''

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
        alerts.append({
            "商品信息": item.get("name", ""),
            "SKU": item.get("sku") or "-",
            "Product Code": item.get("code") or "-",
            "当前库存": estimated_stock,
            "月销量": monthly_sales,
            "预警类型": alert_type,
            "建议": suggestion,
        })
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
        "current_period": {"start": start_date.strftime("%Y-%m-%d"), "end": end_date.strftime("%Y-%m-%d"), **current_summary},
        "previous_period": {"start": previous_start.strftime("%Y-%m-%d"), "end": previous_end.strftime("%Y-%m-%d"), **previous_summary},
        "growth": {
            "quantity": calculate_growth(current_summary["quantity"], previous_summary["quantity"]),
            "revenue": calculate_growth(current_summary["revenue"], previous_summary["revenue"]),
            "orders": calculate_growth(current_summary["orders"], previous_summary["orders"]),
        },
    }


def get_ai_client():
    """获取AI客户端，支持Anthropic和Gemini"""
    # 优先使用Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            from anthropic import Anthropic
            return Anthropic(api_key=anthropic_key), "anthropic", None
        except ImportError:
            return None, "", "anthropic 依赖未安装，请运行: pip install anthropic"
        except Exception as exc:
            logger.exception("Anthropic client init failed")
            return None, "", str(exc)
    
    # 回退到Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        if genai is None:
            return None, "", "google-genai 依赖未安装"
        try:
            return genai.Client(api_key=gemini_key), "gemini", None
        except Exception as exc:
            logger.exception("Gemini client init failed")
            return None, "", str(exc)
    
    return None, "", "ANTHROPIC_API_KEY 或 GEMINI_API_KEY 未配置"


def generate_ai_json(prompt: str) -> Dict:
    client, provider, error = get_ai_client()
    if error:
        raise HTTPException(status_code=503, detail=error)
    
    try:
        if provider == "anthropic":
            # Anthropic API调用
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text if response.content else ""
        else:
            # Gemini API调用
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            text = getattr(response, "text", "") or ""
        
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            return json.loads(json_str)
        else:
            raise ValueError("AI response中未找到有效JSON")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"AI request failed ({provider})")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_PAGE


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
            "ai_enabled": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")),
            "ai_provider": "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "gemini" if os.environ.get("GEMINI_API_KEY") else "none",
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


@app.get("/api/charts/30days")
async def get_30days_charts_data():
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        # 获取过去30天的销售数据
        start_30 = datetime.now() - timedelta(days=30)
        s_ts_30 = int(start_30.timestamp() * 1000)
        e_ts_30 = int(datetime.now().timestamp() * 1000)
        
        raw_sales_all = api.fetch_full_period_sales(s_ts_30, e_ts_30)
        if not raw_sales_all:
            return {"products": [], "period": "过去30天", "message": "过去30天没有销售记录"}
        
        # 使用data_engine处理数据
        df = data_engine.prepare_export_csv(inventory, raw_sales_all)
        
        # 按销售总额排序
        df['销售总额数值'] = df['销售总额'].str.replace('$', '').str.replace(',', '').astype(float)
        df_sorted = df.sort_values('销售总额数值', ascending=False)
        
        return {
            "period": f"{start_30.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            "products": df_sorted.to_dict("records"),
            "total_products": len(df_sorted),
            "total_revenue": df_sorted['销售总额数值'].sum()
        }
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
        result = compare_period_sales(api, [item["id"] for item in matched_items], datetime.strptime(start_date, "%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d"), period)
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


@app.get("/api/categories/overview")
async def get_categories_overview():
    """获取所有类别概览，包含近30天销售商品的分类信息"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        # 获取过去30天的销售数据
        start_30 = datetime.now() - timedelta(days=30)
        s_ts_30 = int(start_30.timestamp() * 1000)
        e_ts_30 = int(datetime.now().timestamp() * 1000)
        
        raw_sales_all = api.fetch_full_period_sales(s_ts_30, e_ts_30)
        if not raw_sales_all:
            return {
                "categories": [],
                "total_products": 0,
                "classified_count": 0,
                "unclassified_count": 0,
                "message": "过去30天没有销售记录"
            }
        
        # 使用data_engine处理数据
        df = data_engine.prepare_export_csv(inventory, raw_sales_all)
        products = df.to_dict("records")
        
        # 统计分类信息
        category_map = {}
        unclassified_products = []
        
        for product in products:
            product_key = f"{product.get('商品信息', '')}|{product.get('SKU', '')}|{product.get('Product Code', '')}"
            
            # 这里需要从前端localStorage读取，后端无法直接访问
            # 所以我们返回产品列表，让前端处理分类统计
            category_map[product_key] = product
        
        return {
            "products": products,
            "total_products": len(products),
            "period": f"{start_30.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            "message": "请在前端加载AI分类库进行分类统计"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/categories/batch-classify")
async def batch_classify_products(payload: Dict):
    """批量分类未分类的商品"""
    products = payload.get("products", [])
    if not products:
        raise HTTPException(status_code=400, detail="No products provided")
    
    results = []
    success_count = 0
    failed_count = 0
    
    for product in products:
        try:
            name = str(product.get("name") or product.get("商品信息") or "").strip()
            if not name:
                failed_count += 1
                continue
            
            classify_payload = {
                "name": name,
                "sku": product.get("sku") or product.get("SKU") or "",
                "code": product.get("code") or product.get("Product Code") or "",
                "price": safe_float(str(product.get("price") or product.get("售价") or "0").replace("$", ""))
            }
            
            classification = await ai_classify(classify_payload)
            results.append({
                "product": product,
                "classification": classification,
                "success": True
            })
            success_count += 1
        except Exception as e:
            results.append({
                "product": product,
                "error": str(e),
                "success": False
            })
            failed_count += 1
    
    return {
        "results": results,
        "success_count": success_count,
        "failed_count": failed_count,
        "total": len(products)
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
