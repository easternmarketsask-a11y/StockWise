# ==============================================================================
# Eastern Market StockWise - 主应用服务器
# 版本：整合版 v2.0（原 app_server.py + web_app.py 优化合并）
# 已废弃：web_app.py, simple_app.py（保留备份，不再维护）
# ==============================================================================

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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from api_handler import CloverAPIHandler
from data_engine import DataEngine
from product_manager import get_product_manager
from ai_results_store import get_ai_results_store
from ai_enhancements import get_ai_enhancements_engine

# Firebase integration (optional - will gracefully fail if not configured)
try:
    from firebase_api_endpoints import firebase_router
    FIREBASE_ENABLED = True
except Exception as e:
    FIREBASE_ENABLED = False
    firebase_router = None
    logging.warning(f"Firebase not available: {e}")

# Import secure configuration
from secure_config import get_anthropic_api_key, get_gemini_api_key

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
        .footer { text-align: center; padding: 20px; color: #64748b; font-size: 14px; }
        /* === Catalog Management === */
        .catalog-toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; padding-bottom: 14px; border-bottom: 1px solid #edf2fa; margin-bottom: 12px; }
        .catalog-toolbar input, .catalog-toolbar select { flex: 1; min-width: 150px; padding: 10px 12px; border-radius: 12px; border: 1px solid #d3ddec; font-size: 13px; }
        .catalog-stats-bar { font-size: 13px; color: #64748b; padding: 4px 0 10px; display: flex; gap: 20px; flex-wrap: wrap; }
        .catalog-stats-bar strong { color: #162033; }
        .catalog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; margin-top: 8px; }
        .catalog-card { background: #fff; border: 1px solid #e5edf9; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(19,45,89,.04); transition: box-shadow .2s, transform .15s; cursor: pointer; }
        .catalog-card:hover { box-shadow: 0 8px 24px rgba(30,99,210,.10); transform: translateY(-2px); }
        .catalog-img-wrap { width: 100%; height: 130px; background: #f7faff; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #eef2fa; overflow: hidden; }
        .catalog-img-wrap img { width: 100%; height: 100%; object-fit: cover; }
        .catalog-img-icon { font-size: 42px; opacity: .15; }
        .catalog-body { padding: 11px 13px; }
        .catalog-name { font-size: 13px; font-weight: 700; color: #162033; margin: 0 0 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .catalog-price { font-size: 16px; font-weight: 800; color: #1e63d2; margin: 3px 0; }
        .catalog-sku { font-size: 11px; color: #94a3b8; }
        .catalog-badges-row { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 7px; }
        .bdg { padding: 3px 7px; border-radius: 999px; font-size: 11px; font-weight: 600; }
        .bdg-blue { background: #eef4ff; color: #214a94; }
        .bdg-green { background: #e9f8ef; color: #2e7d32; }
        .bdg-orange { background: #fff4e5; color: #b26b00; }
        .catalog-footer { padding: 9px 12px; border-top: 1px solid #eef2fa; }
        .btn-edit-prod { width: 100%; padding: 8px; background: #f8fbff; border: 1px solid #d8e3f7; color: #214a94; border-radius: 10px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all .15s; }
        .btn-edit-prod:hover { background: #1e63d2; color: #fff; border-color: #1e63d2; }
        .pub-api-box { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 14px 16px; margin-top: 20px; }
        .pub-api-box h4 { font-size: 13px; font-weight: 700; color: #0369a1; margin: 0 0 8px; }
        .pub-api-box code { background: #e0f2fe; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #0369a1; display: inline-block; margin: 2px 0; }
        /* === Product Detail Modal === */
        .prod-modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.52); z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 16px; }
        .prod-modal-overlay.hidden { display: none; }
        .prod-modal { background: #fff; border-radius: 20px; width: 100%; max-width: 880px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 32px 80px rgba(15,23,42,.22); }
        .prod-modal-head { padding: 18px 22px 14px; border-bottom: 1px solid #edf2fa; display: flex; align-items: flex-start; gap: 14px; flex-shrink: 0; }
        .prod-modal-head-info { flex: 1; min-width: 0; }
        .prod-modal-title { font-size: 17px; font-weight: 700; color: #162033; margin: 0 0 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .prod-modal-sub { font-size: 12px; color: #64748b; margin: 0; }
        .btn-close-modal { background: #f2f5fa; border: 0; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 16px; color: #42526b; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: background .15s; }
        .btn-close-modal:hover { background: #fee2e2; color: #b42318; }
        .prod-modal-tabs { display: flex; gap: 2px; padding: 0 22px; background: #fafcff; border-bottom: 1px solid #edf2fa; flex-shrink: 0; overflow-x: auto; }
        .prod-modal-tab { padding: 10px 14px; background: transparent; border: 0; border-bottom: 3px solid transparent; cursor: pointer; font-size: 13px; font-weight: 600; color: #64748b; transition: all .15s; white-space: nowrap; }
        .prod-modal-tab.active { color: #1e63d2; border-bottom-color: #1e63d2; }
        .prod-modal-tab:hover { color: #1e63d2; }
        .prod-modal-body { flex: 1; overflow-y: auto; padding: 18px 22px; }
        .prod-modal-footer { padding: 12px 22px; border-top: 1px solid #edf2fa; display: flex; gap: 10px; align-items: center; background: #fafcff; border-radius: 0 0 20px 20px; flex-shrink: 0; }
        .prod-modal-footer .mflex { flex: 1; font-size: 13px; }
        .fgrp { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
        .fgrp label { font-size: 11px; font-weight: 700; color: #4f5f78; text-transform: uppercase; letter-spacing: .06em; }
        .fgrp input, .fgrp select, .fgrp textarea { padding: 9px 11px; border: 1px solid #d3ddec; border-radius: 10px; font-size: 13px; color: #162033; width: 100%; resize: vertical; font-family: inherit; background: #fff; }
        .fgrp input:focus, .fgrp select:focus, .fgrp textarea:focus { outline: none; border-color: #8eb4f3; box-shadow: 0 0 0 3px rgba(30,99,210,.08); }
        .fgrp .readonly { background: #f7faff !important; color: #64748b !important; }
        .fgrid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .fgrid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
        .sec-head { font-size: 13px; font-weight: 700; color: #42526b; margin: 18px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #edf2fa; display: flex; align-items: center; gap: 8px; }
        .sec-head:first-child { margin-top: 0; }
        .clover-tag { font-size: 11px; background: #f2f7ff; color: #7a879b; padding: 2px 8px; border-radius: 999px; font-weight: 600; }
        .img-preview-area { width: 100%; height: 170px; background: #f7faff; border: 2px dashed #d3ddec; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; overflow: hidden; transition: border-color .2s; }
        .img-preview-area img { width: 100%; height: 100%; object-fit: contain; }
        .img-no-img { text-align: center; color: #94a3b8; }
        .img-no-img span { font-size: 44px; display: block; opacity: .3; }
        .ai-block { background: #f8fbff; border: 1px solid #dbe7f8; border-radius: 12px; padding: 13px; margin-top: 10px; }
        .ai-block h5 { font-size: 13px; font-weight: 700; color: #214a94; margin: 0 0 10px; }
        @media (max-width: 900px) { .container { flex-direction: column; } .sidebar { width: 100%; } .sidebar-shell { position: static; padding: 14px; } .tabs { flex-direction: row; flex-wrap: wrap; } .tab-button { flex: 1 1 auto; text-align: center; } .cards, .grid-2, .grid-3, .metrics, .hero, .search-layout, .detail-grid { grid-template-columns: 1fr; } .header-inner { flex-direction: column; align-items: flex-start; } .header { padding: 16px 18px; } .header-badge, .panel-meta { display: none; } .panel-header { padding-bottom: 12px; margin-bottom: 16px; } .product-top { flex-direction: column; } .product-actions { width: 100%; } .two-column-actions { grid-template-columns: 1fr 1fr; } }
        /* === Catalog Selection & Batch AI Panel === */
        .catalog-card { position: relative; }
        .catalog-card.cat-selected { border: 2px solid #1e63d2 !important; background: #eef5ff !important; box-shadow: 0 0 0 3px rgba(30,99,210,.15) !important; }
        .catalog-cb-wrap { position: absolute; top: 8px; left: 8px; z-index: 3; }
        .catalog-cb-wrap input[type=checkbox] { width: 18px; height: 18px; cursor: pointer; accent-color: #1e63d2; }
        #catalogSelToolbar { display: none; background: linear-gradient(135deg,#1e3a8a,#1e63d2); color: #fff; border-radius: 12px; padding: 12px 18px; margin: 10px 0; align-items: center; gap: 10px; flex-wrap: wrap; }
        #catalogSelToolbar.visible { display: flex; }
        .cst-count { font-weight: 700; font-size: 14px; flex: 1; min-width: 120px; }
        .cst-ai-select { border-radius: 8px; padding: 7px 10px; border: 1px solid rgba(255,255,255,.35); background: rgba(255,255,255,.15); color: #fff; font-size: 13px; cursor: pointer; }
        .cst-ai-select option { background: #1e3a8a; color: #fff; }
        .cst-btn { background: rgba(255,255,255,.18); color: #fff; border: 1px solid rgba(255,255,255,.3); border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: 13px; font-weight: 600; transition: background .15s; white-space: nowrap; }
        .cst-btn:hover { background: rgba(255,255,255,.3); }
        .cst-btn.cst-primary { background: #fff; color: #1e3a8a; }
        .cst-btn.cst-primary:hover { background: #f0f4ff; }
        .cst-btn:disabled { opacity: .5; cursor: not-allowed; }
        #catalogAIPanel { display: none; border: 1px solid #d0daf0; border-radius: 14px; padding: 20px; margin-top: 14px; background: #f8fbff; }
        #catalogAIPanel.visible { display: block; }
        #catalogAIPanel h4 { margin: 0 0 12px; font-size: 16px; font-weight: 700; color: #162033; }
        .cai-progress-bar { background: #dbeafe; border-radius: 8px; height: 10px; overflow: hidden; margin: 10px 0 4px; }
        .cai-progress-fill { height: 100%; background: #1e63d2; border-radius: 8px; transition: width .4s ease; }
        .cai-progress-text { font-size: 13px; color: #64748b; margin-bottom: 14px; }
        .cai-result-card { background: #fff; border: 1px solid #e6ecf5; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
        .cai-result-card.cai-ok { border-left: 4px solid #2e7d32; }
        .cai-result-card.cai-err { border-left: 4px solid #b42318; }
        .cai-result-name { font-weight: 700; font-size: 14px; color: #162033; margin-bottom: 6px; }
        .cai-result-meta { font-size: 12px; color: #64748b; margin-bottom: 8px; }
        .cai-result-body { font-size: 13px; color: #374151; line-height: 1.6; }
        .cai-result-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
        .cai-result-tag { background: #dbeafe; color: #1e40af; border-radius: 5px; padding: 2px 8px; font-size: 12px; }
        .cai-result-tag.green { background: #dcfce7; color: #166534; }
        .cai-result-tag.orange { background: #fed7aa; color: #9a3412; }
        .cai-export-btn { margin-top: 14px; background: #1e63d2; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }
        .cai-export-btn:hover { background: #1748b3; }
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
                    <button class="tab-button" data-tab="management">🛠️ 商品管理</button>
                    <button class="tab-button" data-tab="batch">⚙️ 批量处理</button>
                    <button class="tab-button" data-tab="analytics">📊 数据分析</button>
                    <button class="tab-button" data-tab="firebase">🔥 Firebase</button>
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
        <section id="management" class="tab-panel card">
            <div class="panel-header">
                <div class="panel-copy">
                    <div class="panel-kicker">Product Management</div>
                    <h2 class="panel-title">🛠️ 商品管理</h2>
                    <p class="muted">管理商品信息、编辑AI处理结果、生成食谱推荐和商品图片提示词。所有数据保存在后端。</p>
                </div>
                <div class="panel-meta">编辑 · 导出 · AI增强</div>
            </div>
            <div class="tabs" style="flex-direction: row; margin-bottom: 20px;">
                <button class="chip active" data-subtab="products-mgmt">📝 商品编辑</button>
                <button class="chip" data-subtab="ai-results-mgmt">🤖 AI结果管理</button>
                <button class="chip" data-subtab="recipe-gen">🍳 食谱生成</button>
                <button class="chip" data-subtab="image-gen">🖼️ 图片提示词</button>
            </div>
            <div id="products-mgmt-panel" class="subtab-panel">
                <div class="catalog-toolbar">
                    <button class="btn" id="loadProductsButton">🔄 同步Clover商品</button>
                    <input id="catalogSearch" placeholder="搜索商品名称 / SKU / 条码...">
                    <select id="catalogCategoryFilter"><option value="">全部分类</option></select>
                    <select id="catalogStatusFilter">
                        <option value="">全部状态</option>
                        <option value="complete">资料已完善</option>
                        <option value="pending">待完善资料</option>
                    </select>
                    <button class="btn secondary" id="exportProductsButton">📥 导出JSON</button>
                    <button class="btn secondary" id="exportMergedButton">📦 导出完整</button>
                </div>
                <div id="productMgmtStatus" class="status"></div>
                <div id="catalogStatsBar" class="catalog-stats-bar" style="display:none;"></div>
                <div id="productMgmtMetrics" class="metrics" style="display:none;"></div>
                <div id="catalogSelToolbar">
                    <span class="cst-count" id="catalogSelCount">已选 0 个商品</span>
                    <select id="catalogAIType" class="cst-ai-select">
                        <option value="classify">🏷️ AI 商品分类</option>
                        <option value="describe">📝 AI 商品描述</option>
                        <option value="recipe">🍳 AI 食谱推荐</option>
                        <option value="image">🖼️ AI 图片提示词</option>
                    </select>
                    <button class="cst-btn cst-primary" id="catalogRunAIBtn">▶ 开始AI处理</button>
                    <button class="cst-btn" id="catalogSelAllBtn">☑ 全选当前筛选</button>
                    <button class="cst-btn" id="catalogSelClearBtn">✕ 取消选择</button>
                </div>
                <div id="productsList">
                    <div class="empty-state">
                        <div class="empty-state-icon">🛒</div>
                        <strong>点击"同步Clover商品"加载完整商品目录</strong>
                        <p class="muted-small" style="margin-top:8px;">系统将从Clover POS拉取全部商品，并合并本地编辑与AI处理结果</p>
                    </div>
                </div>
                <div id="catalogAIPanel">
                    <h4 id="catalogAIPanelTitle">🤖 AI 处理结果</h4>
                    <div id="catalogAIStatus" class="status"></div>
                    <div class="cai-progress-bar" id="catalogAIProgressBar" style="display:none;"><div class="cai-progress-fill" id="catalogAIProgressFill" style="width:0%"></div></div>
                    <div class="cai-progress-text" id="catalogAIProgressText"></div>
                    <div id="catalogAIResultsList"></div>
                    <button class="cai-export-btn" id="catalogAIExportBtn" style="display:none">💾 导出AI结果 JSON</button>
                </div>
                <div class="pub-api-box">
                    <h4>🌐 超市网页公共调用API</h4>
                    <p class="muted-small">以下端点可供超市网站按需调用商品信息（含AI数据，无需鉴权）：</p>
                    <div style="margin-top:8px;display:flex;flex-direction:column;gap:5px;">
                        <div><code>/api/public/products</code> — 全部商品列表（含本地编辑+AI数据）</div>
                        <div><code>/api/public/products/{id}</code> — 单个商品完整详情</div>
                        <div><code>/api/public/products?category=蔬菜</code> — 按分类筛选</div>
                        <div><code>/api/public/products?search=苹果&amp;limit=20</code> — 关键词搜索+分页</div>
                    </div>
                </div>
            </div>
            <div id="ai-results-mgmt-panel" class="subtab-panel" style="display:none;">
                <div class="actions">
                    <button class="btn" id="loadAiResultsButton">加载AI结果</button>
                    <button class="btn secondary" id="exportAiResultsButton">导出AI结果</button>
                </div>
                <div id="aiResultsMgmtStatus" class="status"></div>
                <div id="aiResultsMgmtMetrics" class="metrics"></div>
                <div id="aiResultsList"></div>
            </div>
            <div id="recipe-gen-panel" class="subtab-panel" style="display:none;">
                <div class="grid-2">
                    <div class="detail-section">
                        <h3>生成食谱推荐</h3>
                        <div><label for="recipeProductName">商品名称</label><input id="recipeProductName" placeholder="输入商品名称"></div>
                        <div class="section-gap"><label for="recipeType">食谱类型</label><select id="recipeType"><option value="simple">简单易做</option><option value="detailed">详细步骤</option><option value="creative">创意料理</option></select></div>
                        <div class="actions"><button class="btn" id="generateRecipeButton">生成食谱</button></div>
                    </div>
                    <div class="detail-section">
                        <h3>批量生成</h3>
                        <p class="muted-small">从销量查询中勾选商品，然后在这里批量生成食谱。</p>
                        <div class="section-gap"><label for="batchRecipeType">食谱类型</label><select id="batchRecipeType"><option value="simple">简单易做</option><option value="detailed">详细步骤</option><option value="creative">创意料理</option></select></div>
                        <div class="actions"><button class="btn" id="batchRecipeButton">批量生成食谱</button></div>
                    </div>
                </div>
                <div id="recipeStatus" class="status"></div>
                <div id="recipeResults"></div>
            </div>
            <div id="image-gen-panel" class="subtab-panel" style="display:none;">
                <div class="grid-2">
                    <div class="detail-section">
                        <h3>生成图片提示词</h3>
                        <div><label for="imageProductName">商品名称</label><input id="imageProductName" placeholder="输入商品名称"></div>
                        <div class="section-gap"><label for="imageStyle">图片风格</label><select id="imageStyle"><option value="realistic">真实摄影</option><option value="artistic">艺术插画</option><option value="minimalist">极简主义</option><option value="lifestyle">生活场景</option></select></div>
                        <div class="actions"><button class="btn" id="generateImageButton">生成提示词</button></div>
                    </div>
                    <div class="detail-section">
                        <h3>批量生成</h3>
                        <p class="muted-small">从销量查询中勾选商品，然后在这里批量生成图片提示词。</p>
                        <div class="section-gap"><label for="batchImageStyle">图片风格</label><select id="batchImageStyle"><option value="realistic">真实摄影</option><option value="artistic">艺术插画</option><option value="minimalist">极简主义</option><option value="lifestyle">生活场景</option></select></div>
                        <div class="actions"><button class="btn" id="batchImageButton">批量生成提示词</button></div>
                    </div>
                </div>
                <div id="imageStatus" class="status"></div>
                <div id="imageResults"></div>
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
        <section id="firebase" class="tab-panel card">
            <div class="panel-header">
                <div class="panel-copy">
                    <div class="panel-kicker">Firebase Cloud Storage</div>
                    <h2 class="panel-title">🔥 Firebase 商品管理</h2>
                    <p class="muted">基于 Firestore 和 Cloud Storage 的现代化商品管理系统，支持图片上传和实时数据同步。</p>
                </div>
                <div class="panel-meta">存储 · 同步 · 管理</div>
            </div>
            <div class="tabs" style="flex-direction: row; margin-bottom: 20px;">
                <button class="chip active" data-subtab="firebase-products">📦 商品列表</button>
                <button class="chip" data-subtab="firebase-create">➕ 创建商品</button>
                <button class="chip" data-subtab="firebase-sync">🔄 数据同步</button>
                <button class="chip" data-subtab="firebase-stats">📊 统计信息</button>
            </div>
            <div id="firebase-products-panel" class="subtab-panel">
                <div class="grid-2">
                    <div><label for="firebaseSearch">搜索商品</label><input id="firebaseSearch" placeholder="输入商品名称、SKU或编码"></div>
                    <div><label for="firebaseCategory">分类筛选</label><select id="firebaseCategory"><option value="">全部分类</option></select></div>
                </div>
                <div class="actions">
                    <button class="btn" id="firebaseSearchButton">🔍 搜索</button>
                    <button class="btn secondary" id="firebaseLoadAllButton">📋 加载全部</button>
                    <button class="btn secondary" id="firebaseExportButton">💾 导出数据</button>
                </div>
                <div id="firebaseStatus" class="status"></div>
                <div id="firebaseResults"></div>
            </div>
            <div id="firebase-create-panel" class="subtab-panel" style="display:none;">
                <form id="firebaseCreateForm">
                    <div class="grid-2">
                        <div><label for="firebaseName">商品名称 *</label><input id="firebaseName" required></div>
                        <div><label for="firebasePrice">价格 *</label><input id="firebasePrice" type="number" step="0.01" required></div>
                    </div>
                    <div class="grid-2">
                        <div><label for="firebaseSku">SKU</label><input id="firebaseSku"></div>
                        <div><label for="firebaseCode">条码</label><input id="firebaseCode"></div>
                    </div>
                    <div class="grid-2">
                        <div><label for="firebaseCategory">分类</label><input id="firebaseCategoryCreate"></div>
                        <div><label for="firebaseStock">库存数量</label><input id="firebaseStock" type="number" value="0"></div>
                    </div>
                    <div><label for="firebaseDescription">商品描述</label><textarea id="firebaseDescription" rows="3"></textarea></div>
                    <div><label for="firebaseImage">商品图片</label><input id="firebaseImage" type="file" accept="image/*"></div>
                    <div class="actions">
                        <button class="btn" type="submit">➕ 创建商品</button>
                        <button class="btn secondary" type="reset">🔄 重置表单</button>
                    </div>
                </form>
                <div id="firebaseCreateStatus" class="status"></div>
            </div>
            <div id="firebase-sync-panel" class="subtab-panel" style="display:none;">
                <div class="card">
                    <h3>🔄 Clover 数据同步</h3>
                    <p class="muted">从 Clover POS API 同步商品数据到 Firebase Firestore。</p>
                    <div class="actions">
                        <button class="btn" id="firebaseSyncButton">🚀 开始同步</button>
                        <button class="btn secondary" id="firebaseSyncOverwriteButton">🔄 强制覆盖同步</button>
                    </div>
                    <div id="firebaseSyncStatus" class="status"></div>
                    <div id="firebaseSyncResults"></div>
                </div>
            </div>
            <div id="firebase-stats-panel" class="subtab-panel" style="display:none;">
                <div class="actions"><button class="btn" id="firebaseStatsButton">📊 刷新统计</button></div>
                <div id="firebaseStatsStatus" class="status"></div>
                <div id="firebaseStatsResults"></div>
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

    <!-- ===== Product Detail Modal ===== -->
    <div id="prodModalOverlay" class="prod-modal-overlay hidden">
        <div class="prod-modal" role="dialog" aria-modal="true">
            <div class="prod-modal-head">
                <div class="prod-modal-head-info">
                    <h2 class="prod-modal-title" id="prodModalTitle">商品详情</h2>
                    <p class="prod-modal-sub" id="prodModalSub">SKU: — | Code: — | Clover ID: —</p>
                </div>
                <button class="btn-close-modal" id="prodModalClose" title="关闭">✕</button>
            </div>
            <div class="prod-modal-tabs">
                <button class="prod-modal-tab active" data-modal-tab="basic">📋 基本信息</button>
                <button class="prod-modal-tab" data-modal-tab="images">🖼️ 图片管理</button>
                <button class="prod-modal-tab" data-modal-tab="detail">📝 描述与标签</button>
                <button class="prod-modal-tab" data-modal-tab="ai">🤖 AI 数据</button>
            </div>
            <div class="prod-modal-body" id="prodModalBody"></div>
            <div class="prod-modal-footer">
                <div class="mflex" id="prodModalSaveStatus"></div>
                <button class="btn secondary" id="prodModalCancel">取消</button>
                <button class="btn" id="prodModalSave">💾 保存本地（不写入Clover）</button>
            </div>
        </div>
    </div>
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
        // === Catalog management state ===
        let catalogAll = [];
        let catalogFiltered = [];
        let modalProduct = null;
        let catalogSelected = new Set();
        let catalogAILastResults = [];

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
            if (tabId === 'firebase') initFirebaseTab();
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
        
        async function hasCloudAIResult(product, resultType) {
            try {
                const response = await fetch(`/api/firebase/ai/results?product=${encodeURIComponent(JSON.stringify(product))}&result_type=${resultType}`);
                const data = await response.json();
                return data.success && data.result !== null;
            } catch (error) {
                console.warn('Error checking cloud AI result:', error);
                return false;
            }
        }
        
        async function syncAIResultsFromCloud() {
            try {
                const response = await fetch('/api/firebase/ai/results/all?limit=100');
                const data = await response.json();
                
                if (data.success) {
                    // Merge cloud results with local library
                    data.results.forEach(cloudResult => {
                        const key = cloudResult.product_key;
                        const existingLocal = state.aiLibrary.find(item => 
                            item.type === cloudResult.result_type && item.key === key
                        );
                        
                        if (!existingLocal) {
                            // Add cloud result to local library if not exists
                            state.aiLibrary.unshift({
                                type: cloudResult.result_type,
                                key: key,
                                product: cloudResult.product_data,
                                result: cloudResult.result,
                                createdAt: cloudResult.created_at,
                            });
                        }
                    });
                    
                    saveToStorage(STORAGE_KEYS.AI_LIBRARY, state.aiLibrary);
                    console.log(`Synced ${data.results.length} AI results from cloud`);
                }
            } catch (error) {
                console.warn('Error syncing AI results from cloud:', error);
            }
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
            
            // Also save to Firebase for cloud sync
            saveAIResultToFirebase(product, type, payload);
        }
        
        async function saveAIResultToFirebase(product, resultType, resultData) {
            try {
                const response = await fetch('/api/firebase/ai/results/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        product: product,
                        result_type: resultType,
                        result_data: resultData
                    })
                });
                
                if (!response.ok) {
                    console.warn('Failed to save AI result to Firebase:', await response.text());
                }
            } catch (error) {
                console.warn('Error saving AI result to Firebase:', error);
            }
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
                </div>
            ` : '<div class="empty-state"><div class="empty-state-icon">⚙️</div><strong>批量队列为空</strong>请在销量查询中勾选商品后加入队列。</div>';
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
            const aiAvailabilityEl = document.getElementById('aiAvailability');
            if (aiAvailabilityEl) aiAvailabilityEl.textContent = availability;
        }).catch(() => {
            const aiAvailabilityEl = document.getElementById('aiAvailability');
            if (aiAvailabilityEl) aiAvailabilityEl.textContent = '状态未知';
        });

        // ============================================================================
        // NEW FEATURE HANDLERS - Product Management & Enhanced AI
        // ============================================================================

        // === CATALOG MANAGEMENT TAB HANDLERS ===
        document.getElementById('loadProductsButton').addEventListener('click', async function() {
            setStatus('productMgmtStatus', '🔄 正在从 Clover POS 同步商品目录，请稍候...', 'info');
            this.disabled = true;
            try {
                const data = await requestJson('/api/products/catalog');
                catalogAll = data.products || [];
                catalogFiltered = [...catalogAll];
                const catSel = document.getElementById('catalogCategoryFilter');
                catSel.innerHTML = '<option value="">全部分类</option>';
                (data.categories || []).forEach(cat => {
                    const opt = document.createElement('option');
                    opt.value = cat; opt.textContent = cat;
                    catSel.appendChild(opt);
                });
                setStatus('productMgmtStatus', '✅ 已同步 ' + catalogAll.length + ' 个商品（来自 Clover POS）', 'success');
                renderCatalogGrid();
            } catch (error) {
                setStatus('productMgmtStatus', '❌ ' + error.message, 'error');
            } finally {
                this.disabled = false;
            }
        });

        document.getElementById('catalogSearch').addEventListener('input', filterCatalog);
        document.getElementById('catalogCategoryFilter').addEventListener('change', filterCatalog);
        document.getElementById('catalogStatusFilter').addEventListener('change', filterCatalog);

        document.getElementById('productsList').addEventListener('click', function(e) {
            if (e.target.closest('.catalog-cb-wrap')) return;
            const target = e.target.closest('[data-product-id]');
            if (target) openProductModal(target.dataset.productId);
        });

        function filterCatalog() {
            const search = (document.getElementById('catalogSearch').value || '').toLowerCase();
            const cat = document.getElementById('catalogCategoryFilter').value;
            const status = document.getElementById('catalogStatusFilter').value;
            catalogFiltered = catalogAll.filter(p => {
                if (search) {
                    const name = (p.display_name || p.name || '').toLowerCase();
                    if (!name.includes(search) && !(p.sku||'').toLowerCase().includes(search) && !(p.code||'').toLowerCase().includes(search)) return false;
                }
                if (cat) {
                    const pcat = p.category || (p.ai_classification && p.ai_classification.main_category) || '';
                    if (pcat !== cat) return false;
                }
                if (status) {
                    const hasDesc = !!(p.description || (p.ai_description && p.ai_description.description));
                    if (status === 'complete' && !hasDesc) return false;
                    if (status === 'pending' && hasDesc) return false;
                }
                return true;
            });
            renderCatalogGrid();
        }

        function renderCatalogGrid() {
            const container = document.getElementById('productsList');
            const statsBar = document.getElementById('catalogStatsBar');
            if (!catalogFiltered.length) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🔍</div><strong>没有匹配的商品</strong></div>';
                statsBar.style.display = 'none';
                return;
            }
            statsBar.style.display = 'flex';
            const withImg = catalogFiltered.filter(p => p.image_url).length;
            const withDesc = catalogFiltered.filter(p => p.description || (p.ai_description && p.ai_description.description)).length;
            const withAI = catalogFiltered.filter(p => p.ai_classification || p.ai_description).length;
            statsBar.innerHTML = '显示 <strong>' + catalogFiltered.length + '</strong> / 共 <strong>' + catalogAll.length + '</strong> 个商品 &nbsp;|&nbsp; 🖼️ 有图片 <strong>' + withImg + '</strong> &nbsp;|&nbsp; 📝 有描述 <strong>' + withDesc + '</strong> &nbsp;|&nbsp; 🤖 AI处理 <strong>' + withAI + '</strong>';
            const cards = catalogFiltered.map(p => {
                const name = escHtml(p.display_name || p.name || '未命名商品');
                const price = p.price != null ? '$' + Number(p.price).toFixed(2) : '—';
                const cat = p.category || (p.ai_classification && p.ai_classification.main_category) || '';
                const hasDesc = !!(p.description || (p.ai_description && p.ai_description.description));
                const hasAI = !!(p.ai_classification || p.ai_description);
                const hasImg = !!p.image_url;
                const pid = escHtml(p.id || '');
                const isSel = catalogSelected.has(p.id || '');
                const imgHtml = hasImg
                    ? '<img src="' + escHtml(p.image_url) + '" alt="' + name + '" style="width:100%;height:100%;object-fit:cover;" onerror="this.parentElement.innerHTML=\'<div class=catalog-img-icon>🛒</div>\'">'
                    : '<div class="catalog-img-icon">🛒</div>';
                return '<div class="catalog-card' + (isSel ? ' cat-selected' : '') + '" data-product-id="' + pid + '">' +
                    '<div class="catalog-cb-wrap"><input type="checkbox" class="catalog-cb"' + (isSel ? ' checked' : '') + ' onclick="event.stopPropagation();toggleCatalogCard(\'' + pid + '\')" title="勾选进行AI批量处理"></div>' +
                    '<div class="catalog-img-wrap">' + imgHtml + '</div>' +
                    '<div class="catalog-body">' +
                        '<div class="catalog-name" title="' + name + '">' + name + '</div>' +
                        '<div class="catalog-price">' + price + '</div>' +
                        '<div class="catalog-sku">SKU: ' + escHtml(p.sku || '—') + ' | ' + escHtml(p.code || '—') + '</div>' +
                        '<div class="catalog-badges-row">' +
                            (cat ? '<span class="bdg bdg-blue">' + escHtml(cat) + '</span>' : '') +
                            (hasDesc ? '<span class="bdg bdg-green">✓ 描述</span>' : '') +
                            (hasAI ? '<span class="bdg bdg-orange">✓ AI</span>' : '') +
                            (hasImg ? '<span class="bdg bdg-green">✓ 图片</span>' : '') +
                        '</div>' +
                    '</div>' +
                    '<div class="catalog-footer"><button class="btn-edit-prod" data-product-id="' + pid + '">✏️ 编辑详情</button></div>' +
                '</div>';
            }).join('');
            container.innerHTML = '<div class="catalog-grid">' + cards + '</div>';
        }

        // === Catalog Selection & AI Processing ===
        function toggleCatalogCard(productId) {
            if (!productId) return;
            if (catalogSelected.has(productId)) {
                catalogSelected.delete(productId);
            } else {
                catalogSelected.add(productId);
            }
            const card = document.querySelector('.catalog-card[data-product-id="' + productId + '"]');
            if (card) {
                card.classList.toggle('cat-selected', catalogSelected.has(productId));
                const cb = card.querySelector('.catalog-cb');
                if (cb) cb.checked = catalogSelected.has(productId);
            }
            updateCatalogSelToolbar();
        }

        function updateCatalogSelToolbar() {
            const toolbar = document.getElementById('catalogSelToolbar');
            const countEl = document.getElementById('catalogSelCount');
            if (!toolbar) return;
            const count = catalogSelected.size;
            if (count > 0) {
                toolbar.classList.add('visible');
                countEl.textContent = '已选 ' + count + ' 个商品';
            } else {
                toolbar.classList.remove('visible');
            }
        }

        async function runCatalogAI() {
            const type = document.getElementById('catalogAIType').value;
            const selectedIds = Array.from(catalogSelected);
            if (!selectedIds.length) {
                setStatus('productMgmtStatus', '请先勾选商品再执行AI处理。', 'error');
                return;
            }
            const products = catalogAll.filter(p => p.id && selectedIds.includes(p.id));
            const typeLabels = { classify: 'AI商品分类', describe: 'AI商品描述', recipe: 'AI食谱推荐', image: 'AI图片提示词' };
            const panel = document.getElementById('catalogAIPanel');
            const titleEl = document.getElementById('catalogAIPanelTitle');
            const aiSt = document.getElementById('catalogAIStatus');
            const progressBar = document.getElementById('catalogAIProgressBar');
            const progressFill = document.getElementById('catalogAIProgressFill');
            const progressText = document.getElementById('catalogAIProgressText');
            const resultsList = document.getElementById('catalogAIResultsList');
            const exportBtn = document.getElementById('catalogAIExportBtn');
            const runBtn = document.getElementById('catalogRunAIBtn');

            panel.classList.add('visible');
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            titleEl.textContent = '🤖 ' + (typeLabels[type] || 'AI处理') + ' — 处理中...';
            aiSt.className = 'status info';
            aiSt.textContent = '正在处理 ' + products.length + ' 个商品，请稍候...';
            progressBar.style.display = 'block';
            progressFill.style.width = '0%';
            resultsList.innerHTML = '';
            exportBtn.style.display = 'none';
            runBtn.disabled = true;

            let successCount = 0, failCount = 0;
            catalogAILastResults = [];

            for (let i = 0; i < products.length; i++) {
                const p = products[i];
                const pct = Math.round(((i + 1) / products.length) * 100);
                progressFill.style.width = pct + '%';
                progressText.textContent = '处理中 ' + (i + 1) + '/' + products.length + '：' + escHtml(p.display_name || p.name || '');
                const payload = { name: p.display_name || p.name || '', sku: p.sku || '', code: p.code || '', price: p.price || 0 };
                try {
                    let result = null;
                    if (type === 'classify') {
                        result = await requestJson('/api/ai/classify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                        await requestJson('/api/products/' + p.id + '/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clover_id: p.id, ai_classification_edit: { main_category: result.main_category || '', sub_category: result.sub_category || '', attributes: result.attributes || [] } }) });
                        const idx = catalogAll.findIndex(x => x.id === p.id);
                        if (idx >= 0) catalogAll[idx].ai_classification = result;
                    } else if (type === 'describe') {
                        result = await requestJson('/api/ai/describe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                        await requestJson('/api/products/' + p.id + '/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clover_id: p.id, description: result.description || '', ai_description_edit: { description: result.description || '', selling_points: result.selling_points || [], keywords: result.keywords || [] } }) });
                        const idx = catalogAll.findIndex(x => x.id === p.id);
                        if (idx >= 0) catalogAll[idx].ai_description = result;
                    } else if (type === 'recipe') {
                        const resp = await requestJson('/api/ai/recipe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ product_info: payload, recipe_type: 'simple' }) });
                        result = resp.recipe;
                        const idx = catalogAll.findIndex(x => x.id === p.id);
                        if (idx >= 0) catalogAll[idx].ai_recipe = result;
                    } else if (type === 'image') {
                        const resp = await requestJson('/api/ai/image-prompt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ product_info: payload, style: 'realistic' }) });
                        result = resp.image_prompt;
                        const idx = catalogAll.findIndex(x => x.id === p.id);
                        if (idx >= 0) catalogAll[idx].ai_image = result;
                    }
                    catalogAILastResults.push({ product: p, result, type, success: true });
                    successCount++;
                    resultsList.insertAdjacentHTML('afterbegin', buildCatalogAIResultCard(type, p, result));
                } catch (err) {
                    catalogAILastResults.push({ product: p, error: err.message, type, success: false });
                    failCount++;
                    resultsList.insertAdjacentHTML('afterbegin',
                        '<div class="cai-result-card cai-err"><div class="cai-result-name">' + escHtml(p.display_name || p.name || '') + '</div>' +
                        '<div class="cai-result-body" style="color:#b42318;">❌ ' + escHtml(err.message) + '</div></div>');
                }
            }

            progressBar.style.display = 'none';
            progressText.textContent = '';
            titleEl.textContent = '🤖 ' + (typeLabels[type] || 'AI处理') + ' — 完成';
            aiSt.className = 'status ' + (failCount > 0 ? 'error' : 'success');
            aiSt.textContent = '处理完成：✅ 成功 ' + successCount + ' 个 / ❌ 失败 ' + failCount + ' 个';
            exportBtn.style.display = 'inline-block';
            runBtn.disabled = false;
            filterCatalog();
        }

        function buildCatalogAIResultCard(type, p, result) {
            const name = escHtml(p.display_name || p.name || '');
            if (type === 'classify') {
                const attrTags = (result.attributes || []).map(a => '<span class="cai-result-tag">' + escHtml(a) + '</span>').join('');
                return '<div class="cai-result-card cai-ok">' +
                    '<div class="cai-result-name">' + name + '</div>' +
                    '<div class="cai-result-tags">' +
                        '<span class="cai-result-tag green">主类: ' + escHtml(result.main_category || '') + '</span>' +
                        '<span class="cai-result-tag">子类: ' + escHtml(result.sub_category || '') + '</span>' +
                        (result.confidence_score ? '<span class="cai-result-tag orange">置信度 ' + Math.round(result.confidence_score * 100) + '%</span>' : '') +
                    '</div>' +
                    (attrTags ? '<div class="cai-result-tags" style="margin-top:4px;">' + attrTags + '</div>' : '') +
                '</div>';
            } else if (type === 'describe') {
                const kwTags = (result.keywords || []).map(k => '<span class="cai-result-tag">' + escHtml(k) + '</span>').join('');
                return '<div class="cai-result-card cai-ok">' +
                    '<div class="cai-result-name">' + name + '</div>' +
                    '<div class="cai-result-body">' + escHtml(result.description || '') + '</div>' +
                    (kwTags ? '<div class="cai-result-tags" style="margin-top:8px;">' + kwTags + '</div>' : '') +
                '</div>';
            } else if (type === 'recipe') {
                return '<div class="cai-result-card cai-ok">' +
                    '<div class="cai-result-name">' + name + '</div>' +
                    '<div class="cai-result-meta">' + escHtml(result.recipe_name || '') + (result.cuisine_type ? ' | ' + escHtml(result.cuisine_type) : '') + (result.cook_time ? ' | 烹饪 ' + result.cook_time + ' 分钟' : '') + '</div>' +
                    '<div class="cai-result-tags">' +
                        (result.difficulty ? '<span class="cai-result-tag green">难度: ' + escHtml(result.difficulty) + '</span>' : '') +
                        (result.servings ? '<span class="cai-result-tag">' + result.servings + ' 人份</span>' : '') +
                    '</div>' +
                '</div>';
            } else if (type === 'image') {
                const promptText = result.prompt_en || result.prompt || '';
                return '<div class="cai-result-card cai-ok">' +
                    '<div class="cai-result-name">' + name + '</div>' +
                    '<div class="cai-result-body" style="background:#f8fbff;padding:8px;border-radius:6px;font-size:12px;word-break:break-all;">' + escHtml(promptText.substring(0, 220)) + (promptText.length > 220 ? '…' : '') + '</div>' +
                    '<div class="cai-result-tags" style="margin-top:6px;"><span class="cai-result-tag">风格: ' + escHtml(result.style || 'realistic') + '</span></div>' +
                '</div>';
            }
            return '';
        }

        function exportCatalogAIResults() {
            if (!catalogAILastResults.length) return;
            const blob = new Blob([JSON.stringify(catalogAILastResults, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'catalog_ai_results_' + new Date().toISOString().slice(0, 10) + '.json';
            a.click();
            URL.revokeObjectURL(url);
        }

        document.getElementById('catalogRunAIBtn').addEventListener('click', runCatalogAI);
        document.getElementById('catalogAIExportBtn').addEventListener('click', exportCatalogAIResults);
        document.getElementById('catalogSelAllBtn').addEventListener('click', function() {
            catalogFiltered.forEach(p => { if (p.id) catalogSelected.add(p.id); });
            renderCatalogGrid();
            updateCatalogSelToolbar();
        });
        document.getElementById('catalogSelClearBtn').addEventListener('click', function() {
            catalogSelected.clear();
            renderCatalogGrid();
            updateCatalogSelToolbar();
        });
        window.toggleCatalogCard = toggleCatalogCard;

        document.getElementById('exportProductsButton').addEventListener('click', async () => {
            try {
                const data = await requestJson('/api/products/export?format=json');
                const blob = new Blob([data.data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `products_export_${new Date().toISOString().slice(0,10)}.json`;
                a.click();
                setStatus('productMgmtStatus', '商品数据已导出', 'success');
            } catch (error) {
                setStatus('productMgmtStatus', error.message, 'error');
            }
        });

        document.getElementById('exportMergedButton').addEventListener('click', async () => {
            try {
                const data = await requestJson('/api/products/merged');
                const blob = new Blob([JSON.stringify(data.products, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `products_merged_${new Date().toISOString().slice(0,10)}.json`;
                a.click();
                setStatus('productMgmtStatus', '完整数据已导出（含AI结果）', 'success');
            } catch (error) {
                setStatus('productMgmtStatus', error.message, 'error');
            }
        });

        // AI Results Management Handlers
        document.getElementById('loadAiResultsButton').addEventListener('click', async () => {
            setStatus('aiResultsMgmtStatus', '正在加载AI结果...', 'info');
            try {
                const data = await requestJson('/api/ai-results');
                setStatus('aiResultsMgmtStatus', `成功加载 ${data.count} 条AI结果`, 'success');
                renderMetrics('aiResultsMgmtMetrics', [
                    { label: '总结果数', value: data.statistics.total_results },
                    { label: '有分类', value: data.statistics.with_classification },
                    { label: '有描述', value: data.statistics.with_description },
                    { label: '有食谱', value: data.statistics.with_recipe }
                ]);
                renderAiResultsList(data.results);
            } catch (error) {
                setStatus('aiResultsMgmtStatus', error.message, 'error');
            }
        });

        document.getElementById('exportAiResultsButton').addEventListener('click', async () => {
            try {
                const data = await requestJson('/api/ai-results/export?format=json');
                const blob = new Blob([data.data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ai_results_export_${new Date().toISOString().slice(0,10)}.json`;
                a.click();
                setStatus('aiResultsMgmtStatus', 'AI结果已导出', 'success');
            } catch (error) {
                setStatus('aiResultsMgmtStatus', error.message, 'error');
            }
        });

        // Recipe Generation Handlers
        document.getElementById('generateRecipeButton').addEventListener('click', async () => {
            const productName = document.getElementById('recipeProductName').value.trim();
            const recipeType = document.getElementById('recipeType').value;
            
            if (!productName) {
                setStatus('recipeStatus', '请输入商品名称', 'error');
                return;
            }
            
            setStatus('recipeStatus', '正在生成食谱推荐...', 'info');
            try {
                const data = await requestJson('/api/ai/recipe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product_info: { name: productName },
                        recipe_type: recipeType
                    })
                });
                setStatus('recipeStatus', '食谱生成成功！', 'success');
                renderRecipeResult(data.recipe);
            } catch (error) {
                setStatus('recipeStatus', error.message, 'error');
            }
        });

        document.getElementById('batchRecipeButton').addEventListener('click', async () => {
            if (state.selectedProducts.length === 0) {
                setStatus('recipeStatus', '请先在销量查询中勾选商品', 'error');
                return;
            }
            
            const recipeType = document.getElementById('batchRecipeType').value;
            setStatus('recipeStatus', `正在为 ${state.selectedProducts.length} 个商品生成食谱...`, 'info');
            
            try {
                const products = state.selectedProducts.map(p => ({
                    name: p['商品信息'],
                    sku: p['SKU'],
                    code: p['Product Code'],
                    price: parseFloat(String(p['售价'] || '0').replace('$', ''))
                }));
                
                const data = await requestJson('/api/ai/batch-recipe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ products, recipe_type: recipeType })
                });
                
                setStatus('recipeStatus', `批量食谱生成完成：成功 ${data.result.success_count} 个，失败 ${data.result.failed_count} 个`, 
                    data.result.failed_count > 0 ? 'error' : 'success');
                renderBatchRecipeResults(data.result.results);
            } catch (error) {
                setStatus('recipeStatus', error.message, 'error');
            }
        });

        // Image Prompt Generation Handlers
        document.getElementById('generateImageButton').addEventListener('click', async () => {
            const productName = document.getElementById('imageProductName').value.trim();
            const style = document.getElementById('imageStyle').value;
            
            if (!productName) {
                setStatus('imageStatus', '请输入商品名称', 'error');
                return;
            }
            
            setStatus('imageStatus', '正在生成图片提示词...', 'info');
            try {
                const data = await requestJson('/api/ai/image-prompt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product_info: { name: productName },
                        style: style
                    })
                });
                setStatus('imageStatus', '图片提示词生成成功！', 'success');
                renderImagePromptResult(data.image_prompt);
            } catch (error) {
                setStatus('imageStatus', error.message, 'error');
            }
        });

        document.getElementById('batchImageButton').addEventListener('click', async () => {
            if (state.selectedProducts.length === 0) {
                setStatus('imageStatus', '请先在销量查询中勾选商品', 'error');
                return;
            }
            
            const style = document.getElementById('batchImageStyle').value;
            setStatus('imageStatus', `正在为 ${state.selectedProducts.length} 个商品生成图片提示词...`, 'info');
            
            try {
                const products = state.selectedProducts.map(p => ({
                    name: p['商品信息'],
                    sku: p['SKU'],
                    code: p['Product Code'],
                    description: p['描述'] || ''
                }));
                
                const data = await requestJson('/api/ai/batch-image-prompt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ products, style })
                });
                
                setStatus('imageStatus', `批量图片提示词生成完成：成功 ${data.result.success_count} 个，失败 ${data.result.failed_count} 个`, 
                    data.result.failed_count > 0 ? 'error' : 'success');
                renderBatchImageResults(data.result.results);
            } catch (error) {
                setStatus('imageStatus', error.message, 'error');
            }
        });

        // Render Functions for New Features
        // renderProductsList is superseded by renderCatalogGrid (catalog management)
        function renderProductsList(products) { renderCatalogGrid(); }

        // ==============================
        // PRODUCT DETAIL MODAL
        // ==============================
        function escHtml(s) {
            return String(s == null ? '' : s)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        function openProductModal(productId) {
            const p = catalogAll.find(x => x.id === productId);
            if (!p) return;
            modalProduct = p;
            document.getElementById('prodModalTitle').textContent = p.display_name || p.name || 'Product Detail';
            document.getElementById('prodModalSub').textContent =
                'SKU: ' + (p.sku || '-') + '  |  Code: ' + (p.code || '-') + '  |  ID: ' + (p.id || '-') + '  |  Clover Price: $' + Number(p.price || 0).toFixed(2);
            document.getElementById('prodModalSaveStatus').textContent = '';
            document.querySelectorAll('.prod-modal-tab').forEach(t => t.classList.remove('active'));
            document.querySelector('[data-modal-tab="basic"]').classList.add('active');
            renderModalTab('basic');
            document.getElementById('prodModalOverlay').classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }

        function closeProductModal() {
            document.getElementById('prodModalOverlay').classList.add('hidden');
            document.body.style.overflow = '';
            modalProduct = null;
        }

        document.getElementById('prodModalClose').addEventListener('click', closeProductModal);
        document.getElementById('prodModalCancel').addEventListener('click', closeProductModal);
        document.getElementById('prodModalOverlay').addEventListener('click', function(e) {
            if (e.target === this) closeProductModal();
        });
        document.querySelectorAll('.prod-modal-tab').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.prod-modal-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                renderModalTab(this.dataset.modalTab);
            });
        });

        function renderModalTab(tab) {
            const p = modalProduct;
            if (!p) return;
            const body = document.getElementById('prodModalBody');
            if (tab === 'basic') {
                body.innerHTML =
                    '<div class="sec-head">Clover POS Data <span class="clover-tag">Read-only from Clover</span></div>' +
                    '<div class="fgrid2">' +
                        '<div class="fgrp"><label>Clover Name</label><input class="readonly" readonly value="' + escHtml(p.name || '') + '"></div>' +
                        '<div class="fgrp"><label>Clover Price</label><input class="readonly" readonly value="$' + Number(p.price || 0).toFixed(2) + '"></div>' +
                        '<div class="fgrp"><label>SKU</label><input class="readonly" readonly value="' + escHtml(p.sku || '') + '"></div>' +
                        '<div class="fgrp"><label>Barcode (Code)</label><input class="readonly" readonly value="' + escHtml(p.code || '') + '"></div>' +
                        '<div class="fgrp"><label>Alt Code</label><input class="readonly" readonly value="' + escHtml(p.alt_code || '') + '"></div>' +
                        '<div class="fgrp"><label>Clover ID</label><input class="readonly" readonly value="' + escHtml(p.id || '') + '"></div>' +
                    '</div>' +
                    '<div class="sec-head" style="margin-top:18px;">Local Edits <span class="clover-tag">Editable - saved locally only</span></div>' +
                    '<div class="fgrid2">' +
                        '<div class="fgrp"><label>Display Name (overrides Clover)</label><input id="ed_display_name" value="' + escHtml(p.display_name || '') + '"></div>' +
                        '<div class="fgrp"><label>Price Note (promo etc.)</label><input id="ed_price_note" value="' + escHtml(p.price_note || '') + '"></div>' +
                        '<div class="fgrp"><label>Category</label><input id="ed_category" value="' + escHtml(p.category || '') + '"></div>' +
                        '<div class="fgrp"><label>Sub-Category</label><input id="ed_subcategory" value="' + escHtml(p.subcategory || '') + '"></div>' +
                        '<div class="fgrp"><label>Brand</label><input id="ed_brand" value="' + escHtml(p.brand || '') + '"></div>' +
                        '<div class="fgrp"><label>Origin / Country</label><input id="ed_origin" value="' + escHtml(p.origin || '') + '"></div>' +
                        '<div class="fgrp"><label>Unit (each / lb / kg)</label><input id="ed_unit" value="' + escHtml(p.unit || '') + '"></div>' +
                        '<div class="fgrp"><label>Weight / Size Spec</label><input id="ed_weight_spec" value="' + escHtml(p.weight_spec || '') + '"></div>' +
                    '</div>' +
                    '<div class="fgrid2" style="margin-top:4px;">' +
                        '<div class="fgrp"><label>Status</label><select id="ed_status">' +
                            '<option value="active"' + ((p.status || 'active') === 'active' ? ' selected' : '') + '>Active (In Stock)</option>' +
                            '<option value="inactive"' + (p.status === 'inactive' ? ' selected' : '') + '>Inactive (Off Shelf)</option>' +
                            '<option value="seasonal"' + (p.status === 'seasonal' ? ' selected' : '') + '>Seasonal</option>' +
                            '<option value="limited"' + (p.status === 'limited' ? ' selected' : '') + '>Limited</option>' +
                        '</select></div>' +
                        '<div class="fgrp"><label>Featured Product</label><select id="ed_featured">' +
                            '<option value="false"' + (!p.featured ? ' selected' : '') + '>No</option>' +
                            '<option value="true"' + (p.featured ? ' selected' : '') + '>Yes (Show in Featured)</option>' +
                        '</select></div>' +
                    '</div>' +
                    '<div class="fgrp" style="margin-top:4px;"><label>Tags (comma-separated: organic, local, gluten-free...)</label>' +
                        '<input id="ed_tags" value="' + escHtml((p.tags || []).join(', ')) + '"></div>' +
                    '<div class="fgrp"><label>Internal Notes</label><textarea id="ed_notes" rows="2">' + escHtml(p.notes || '') + '</textarea></div>';

            } else if (tab === 'images') {
                const imgUrl = p.image_url || '';
                body.innerHTML =
                    '<div class="sec-head">Main Product Image</div>' +
                    '<div class="img-preview-area" id="imgPreviewArea">' +
                        (imgUrl
                            ? '<img src="' + escHtml(imgUrl) + '" alt="product" onerror="this.parentElement.innerHTML=\'<div class=img-no-img><span>no image</span></div>\'">'
                            : '<div class="img-no-img"><span style="font-size:40px;opacity:.2;">🖼️</span><div>No image yet</div></div>') +
                    '</div>' +
                    '<div class="fgrp"><label>Main Image URL</label>' +
                        '<input id="ed_image_url" value="' + escHtml(imgUrl) + '" placeholder="https://example.com/product.jpg"></div>' +
                    '<div class="sec-head">Image Gallery (multiple images, one URL per line)</div>' +
                    '<div class="fgrp"><textarea id="ed_image_gallery" rows="5" placeholder="https://example.com/img1.jpg">' +
                        escHtml((p.image_gallery || []).join('\n')) + '</textarea></div>' +
                    '<p class="muted-small" style="margin-top:8px;">Image URLs will be returned through the public API for your website. ' +
                        'Upload images to Firebase Storage or a CDN first, then paste the URL here. Not written to Clover POS.</p>';
                document.getElementById('ed_image_url').addEventListener('input', function() {
                    const area = document.getElementById('imgPreviewArea');
                    if (this.value) {
                        area.innerHTML = '<img src="' + escHtml(this.value) + '" alt="preview" style="width:100%;height:100%;object-fit:contain;" onerror="this.parentElement.innerHTML=\'<div class=img-no-img><span>Invalid URL</span></div>\'">';
                    } else {
                        area.innerHTML = '<div class="img-no-img"><span style="font-size:40px;opacity:.2;">🖼️</span><div>No image</div></div>';
                    }
                });

            } else if (tab === 'detail') {
                const desc = p.description || (p.ai_description && p.ai_description.description) || '';
                const kw = p.keywords || (p.ai_description && (p.ai_description.keywords || []).join(', ')) || '';
                const sp = p.selling_points || (p.ai_description && (p.ai_description.selling_points || []).join('\n')) || '';
                body.innerHTML =
                    '<div class="sec-head">Product Description</div>' +
                    '<div class="fgrp"><label>Short Description (for listing)</label><textarea id="ed_description" rows="3">' + escHtml(desc) + '</textarea></div>' +
                    '<div class="fgrp"><label>Long Description (for detail page)</label><textarea id="ed_long_description" rows="5">' + escHtml(p.long_description || '') + '</textarea></div>' +
                    '<div class="sec-head">SEO & Search</div>' +
                    '<div class="fgrp"><label>Keywords (comma-separated)</label><input id="ed_keywords" value="' + escHtml(kw) + '"></div>' +
                    '<div class="fgrp"><label>Selling Points (one per line)</label><textarea id="ed_selling_points" rows="4">' + escHtml(sp) + '</textarea></div>' +
                    '<div class="sec-head">Nutrition & Storage</div>' +
                    '<div class="fgrid2">' +
                        '<div class="fgrp"><label>Allergen Info</label><input id="ed_allergens" value="' + escHtml(p.allergens || '') + '"></div>' +
                        '<div class="fgrp"><label>Shelf Life</label><input id="ed_shelf_life" value="' + escHtml(p.shelf_life || '') + '"></div>' +
                        '<div class="fgrp"><label>Storage Instructions</label><input id="ed_storage" value="' + escHtml(p.storage || '') + '"></div>' +
                        '<div class="fgrp"><label>Nutrition Summary</label><input id="ed_nutrition" value="' + escHtml(p.nutrition || '') + '"></div>' +
                    '</div>';

            } else if (tab === 'ai') {
                const cls = p.ai_classification || {};
                const desc = p.ai_description || {};
                const recipe = p.ai_recipe || {};
                const imgP = p.ai_image || {};
                const hasClass = Object.keys(cls).length > 0;
                const hasDesc = Object.keys(desc).length > 0;
                body.innerHTML =
                    '<div class="sec-head">AI Classification</div>' +
                    (hasClass
                        ? '<div class="ai-block"><h5>Category Info</h5>' +
                            '<div class="fgrid2">' +
                                '<div class="fgrp"><label>Main Category</label><input id="ai_main_cat" value="' + escHtml(cls.main_category || '') + '"></div>' +
                                '<div class="fgrp"><label>Sub Category</label><input id="ai_sub_cat" value="' + escHtml(cls.sub_category || '') + '"></div>' +
                            '</div>' +
                            '<div class="fgrp"><label>Attribute Tags</label><input id="ai_attrs" value="' + escHtml((cls.attributes || []).join(', ')) + '"></div></div>'
                        : '<p class="muted-small">No AI classification yet. Use AI Classify in Sales Query tab or Batch Processing.</p>') +
                    '<div class="sec-head" style="margin-top:18px;">AI Description</div>' +
                    (hasDesc
                        ? '<div class="ai-block"><h5>AI-Generated Content</h5>' +
                            '<div class="fgrp"><label>Description</label><textarea id="ai_description" rows="3">' + escHtml(desc.description || '') + '</textarea></div>' +
                            '<div class="fgrp"><label>Selling Points (one per line)</label><textarea id="ai_selling_points" rows="3">' + escHtml((desc.selling_points || []).join('\n')) + '</textarea></div>' +
                            '<div class="fgrp"><label>Keywords</label><input id="ai_keywords" value="' + escHtml((desc.keywords || []).join(', ')) + '"></div></div>'
                        : '<p class="muted-small">No AI description. Use AI Describe in Sales Query tab.</p>') +
                    '<div class="sec-head" style="margin-top:18px;">AI Recipe</div>' +
                    (recipe.recipe_name
                        ? '<div class="ai-block"><h5>' + escHtml(recipe.recipe_name) + '</h5><div class="muted-small">' +
                            escHtml(recipe.cuisine_type || '') + ' - Difficulty: ' + escHtml(recipe.difficulty || '') +
                            ' - Prep: ' + (recipe.prep_time || 0) + 'min - Cook: ' + (recipe.cook_time || 0) + 'min</div></div>'
                        : '<p class="muted-small">No recipe yet. Generate in Product Management - Recipe tab.</p>') +
                    '<div class="sec-head" style="margin-top:18px;">AI Image Prompt</div>' +
                    (imgP.prompt_en
                        ? '<div class="ai-block"><h5>Image Prompt (EN)</h5><div class="muted-small" style="word-break:break-all;">' +
                            escHtml((imgP.prompt_en || '').substring(0, 200)) + ((imgP.prompt_en || '').length > 200 ? '...' : '') + '</div></div>'
                        : '<p class="muted-small">No image prompt. Generate in Product Management - Image Prompt tab.</p>');
            }
        }

        document.getElementById('prodModalSave').addEventListener('click', async function() {
            if (!modalProduct) return;
            const btn = this;
            const statusEl = document.getElementById('prodModalSaveStatus');
            btn.disabled = true;
            statusEl.textContent = 'Saving...';
            statusEl.style.color = '#64748b';
            try {
                const edits = { clover_id: modalProduct.id };
                const strFields = ['display_name','price_note','category','subcategory','brand','origin',
                    'unit','weight_spec','status','notes','image_url','description','long_description',
                    'keywords','allergens','shelf_life','storage','nutrition'];
                strFields.forEach(f => { const el = document.getElementById('ed_' + f); if (el) edits[f] = el.value; });
                const tagsEl = document.getElementById('ed_tags');
                if (tagsEl) edits.tags = tagsEl.value.split(',').map(s => s.trim()).filter(Boolean);
                const galEl = document.getElementById('ed_image_gallery');
                if (galEl) edits.image_gallery = galEl.value.split('\n').map(s => s.trim()).filter(Boolean);
                const spEl = document.getElementById('ed_selling_points');
                if (spEl) edits.selling_points = spEl.value.split('\n').map(s => s.trim()).filter(Boolean);
                const featEl = document.getElementById('ed_featured');
                if (featEl) edits.featured = featEl.value === 'true';
                const aiMC = document.getElementById('ai_main_cat');
                if (aiMC) {
                    edits.ai_classification_edit = {
                        main_category: aiMC.value,
                        sub_category: (document.getElementById('ai_sub_cat') || { value: '' }).value,
                        attributes: ((document.getElementById('ai_attrs') || { value: '' }).value).split(',').map(s => s.trim()).filter(Boolean)
                    };
                }
                const aiDE = document.getElementById('ai_description');
                if (aiDE) {
                    edits.ai_description_edit = {
                        description: aiDE.value,
                        selling_points: ((document.getElementById('ai_selling_points') || { value: '' }).value).split('\n').map(s => s.trim()).filter(Boolean),
                        keywords: ((document.getElementById('ai_keywords') || { value: '' }).value).split(',').map(s => s.trim()).filter(Boolean)
                    };
                }
                const data = await requestJson('/api/products/' + modalProduct.id + '/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(edits)
                });
                if (data.success) {
                    const idx = catalogAll.findIndex(x => x.id === modalProduct.id);
                    if (idx >= 0) { Object.assign(catalogAll[idx], edits); modalProduct = catalogAll[idx]; }
                    document.getElementById('prodModalTitle').textContent = edits.display_name || modalProduct.name || 'Product Detail';
                    statusEl.textContent = 'Saved locally (NOT written to Clover POS)';
                    statusEl.style.color = '#2e7d32';
                    filterCatalog();
                } else {
                    statusEl.textContent = 'Save failed';
                    statusEl.style.color = '#b42318';
                }
            } catch (err) {
                statusEl.textContent = err.message;
                statusEl.style.color = '#b42318';
            } finally {
                btn.disabled = false;
            }
        });

        function renderAiResultsList(results) {
            const container = document.getElementById('aiResultsList');
            if (!results || results.length === 0) {
                container.innerHTML = '<div class="empty-state"><strong>暂无AI结果</strong>点击"加载AI结果"按钮获取数据。</div>';
                return;
            }
            container.innerHTML = `<div class="library-list">${results.map(r => {
                const product = r.product_info || {};
                const hasClass = !!r.classification;
                const hasDesc = !!r.description;
                const hasRecipe = !!r.recipe;
                const hasImage = !!r.image_info;
                return `
                <div class="library-item">
                    <h4>${product.name || '未命名商品'}</h4>
                    <div class="meta">SKU: ${product.sku || 'N/A'} | Code: ${product.code || 'N/A'}</div>
                    <div class="status-badges">
                        ${hasClass ? '<span class="badge success">✓ 已分类</span>' : ''}
                        ${hasDesc ? '<span class="badge success">✓ 已描述</span>' : ''}
                        ${hasRecipe ? '<span class="badge success">✓ 有食谱</span>' : ''}
                        ${hasImage ? '<span class="badge success">✓ 有图片提示</span>' : ''}
                    </div>
                </div>`;
            }).join('')}</div>`;
        }

        function renderRecipeResult(recipe) {
            const container = document.getElementById('recipeResults');
            container.innerHTML = `
                <div class="card" style="margin-top:16px;">
                    <h3>${recipe.recipe_name || '食谱'}</h3>
                    ${recipe.recipe_name_en ? `<p class="muted">${recipe.recipe_name_en}</p>` : ''}
                    <div class="detail-grid" style="margin-top:16px;">
                        <div class="detail-section">
                            <h4>基本信息</h4>
                            <div class="detail-row"><span class="detail-key">菜系</span><span class="detail-value">${recipe.cuisine_type || 'N/A'}</span></div>
                            <div class="detail-row"><span class="detail-key">难度</span><span class="detail-value">${recipe.difficulty || 'N/A'}</span></div>
                            <div class="detail-row"><span class="detail-key">准备时间</span><span class="detail-value">${recipe.prep_time || 'N/A'} 分钟</span></div>
                            <div class="detail-row"><span class="detail-key">烹饪时间</span><span class="detail-value">${recipe.cook_time || 'N/A'} 分钟</span></div>
                            <div class="detail-row"><span class="detail-key">份数</span><span class="detail-value">${recipe.servings || 'N/A'}</span></div>
                        </div>
                        <div class="detail-section">
                            <h4>食材清单</h4>
                            ${(recipe.ingredients || []).map(ing => `
                                <div class="detail-row">
                                    <span class="detail-key">${ing.item}</span>
                                    <span class="detail-value">${ing.amount}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="detail-section" style="margin-top:16px;">
                        <h4>烹饪步骤</h4>
                        ${(recipe.steps || []).map(step => `
                            <div class="detail-block">
                                <strong>步骤 ${step.step}:</strong> ${step.instruction}
                                ${step.tip ? `<div class="muted-small" style="margin-top:4px;">💡 ${step.tip}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                    ${recipe.tips && recipe.tips.length > 0 ? `
                        <div class="detail-section" style="margin-top:16px;">
                            <h4>烹饪技巧</h4>
                            ${recipe.tips.map(tip => `<div class="muted-small">• ${tip}</div>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        function renderBatchRecipeResults(results) {
            const container = document.getElementById('recipeResults');
            const successful = results.filter(r => r.success);
            container.innerHTML = `<div class="library-list" style="margin-top:16px;">${successful.map(r => `
                <div class="library-item">
                    <h4>${r.recipe.recipe_name || '食谱'}</h4>
                    <div class="meta">商品: ${r.product.name}</div>
                    <div class="muted-small" style="margin-top:8px;">
                        ${r.recipe.cuisine_type || ''} | ${r.recipe.difficulty || ''} | 
                        准备 ${r.recipe.prep_time || 0} 分钟 | 烹饪 ${r.recipe.cook_time || 0} 分钟
                    </div>
                </div>
            `).join('')}</div>`;
        }

        function renderImagePromptResult(imagePrompt) {
            const container = document.getElementById('imageResults');
            container.innerHTML = `
                <div class="card" style="margin-top:16px;">
                    <h3>图片生成提示词</h3>
                    <div class="detail-section" style="margin-top:16px;">
                        <h4>英文提示词（推荐）</h4>
                        <div class="detail-value-text" style="background:#f8fbff;padding:12px;border-radius:8px;margin-top:8px;">${imagePrompt.prompt_en || 'N/A'}</div>
                    </div>
                    <div class="detail-section" style="margin-top:16px;">
                        <h4>中文描述</h4>
                        <div class="detail-value-text" style="background:#f8fbff;padding:12px;border-radius:8px;margin-top:8px;">${imagePrompt.prompt_zh || 'N/A'}</div>
                    </div>
                    <div class="detail-grid" style="margin-top:16px;">
                        <div class="detail-section">
                            <h4>参数建议</h4>
                            <div class="detail-row"><span class="detail-key">风格</span><span class="detail-value">${imagePrompt.style || 'N/A'}</span></div>
                            <div class="detail-row"><span class="detail-key">构图</span><span class="detail-value">${imagePrompt.composition || 'N/A'}</span></div>
                            <div class="detail-row"><span class="detail-key">光线</span><span class="detail-value">${imagePrompt.lighting || 'N/A'}</span></div>
                            <div class="detail-row"><span class="detail-key">推荐尺寸</span><span class="detail-value">${imagePrompt.recommended_size || 'N/A'}</span></div>
                        </div>
                        <div class="detail-section">
                            <h4>关键元素</h4>
                            ${(imagePrompt.key_elements || []).map(el => `<div class="muted-small">• ${el}</div>`).join('')}
                            ${imagePrompt.color_palette && imagePrompt.color_palette.length > 0 ? `
                                <div style="margin-top:12px;">
                                    <strong>色彩:</strong> ${imagePrompt.color_palette.join(', ')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    ${imagePrompt.negative_prompt ? `
                        <div class="detail-section" style="margin-top:16px;">
                            <h4>负面提示词</h4>
                            <div class="muted-small">${imagePrompt.negative_prompt}</div>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        function renderBatchImageResults(results) {
            const container = document.getElementById('imageResults');
            const successful = results.filter(r => r.success);
            container.innerHTML = `<div class="library-list" style="margin-top:16px;">${successful.map(r => `
                <div class="library-item">
                    <h4>${r.product.name}</h4>
                    <div class="meta">风格: ${r.image_prompt.style || 'N/A'}</div>
                    <div class="detail-value-text" style="background:#f8fbff;padding:8px;border-radius:6px;margin-top:8px;font-size:13px;">
                        ${r.image_prompt.prompt_en ? r.image_prompt.prompt_en.substring(0, 150) + '...' : 'N/A'}
                    </div>
                </div>
            `).join('')}</div>`;
        }

        setDefaultDates();
        renderBatchCenter();
        renderLibrary();
        syncOverview();
        
        // Sync AI results from Firebase on startup
        syncAIResultsFromCloud();
        
        console.log('StockWise initialized');
        console.log('Batch Queue:', state.batchQueue.length, 'items');
        console.log('AI Library:', state.aiLibrary.length, 'records');
        console.log('Batch Results:', state.batchResults.length, 'tasks');
        
        // Firebase 功能
        let firebaseCategories = [];
        let firebaseProducts = [];
        
        function initFirebaseTab() {
            loadFirebaseCategories();
            bindFirebaseEvents();
        }
        
        function bindFirebaseEvents() {
            // 搜索按钮
            document.getElementById('firebaseSearchButton').addEventListener('click', searchFirebaseProducts);
            document.getElementById('firebaseLoadAllButton').addEventListener('click', loadAllFirebaseProducts);
            document.getElementById('firebaseExportButton').addEventListener('click', exportFirebaseData);
            
            // 创建表单
            document.getElementById('firebaseCreateForm').addEventListener('submit', createFirebaseProduct);
            
            // 同步按钮
            document.getElementById('firebaseSyncButton').addEventListener('click', syncFromClover);
            document.getElementById('firebaseSyncOverwriteButton').addEventListener('click', () => syncFromClover(true));
            
            // 统计按钮
            document.getElementById('firebaseStatsButton').addEventListener('click', loadFirebaseStats);
        }
        
        async function loadFirebaseCategories() {
            try {
                const response = await fetch('/api/firebase/categories');
                const data = await response.json();
                
                if (data.success) {
                    firebaseCategories = data.categories;
                    const select = document.getElementById('firebaseCategory');
                    select.innerHTML = '<option value="">全部分类</option>';
                    firebaseCategories.forEach(cat => {
                        select.innerHTML += `<option value="${cat}">${cat}</option>`;
                    });
                }
            } catch (error) {
                console.error('加载分类失败:', error);
            }
        }
        
        async function searchFirebaseProducts() {
            const searchTerm = document.getElementById('firebaseSearch').value;
            const category = document.getElementById('firebaseCategory').value;
            const status = document.getElementById('firebaseStatus');
            const results = document.getElementById('firebaseResults');
            
            status.innerHTML = '🔍 搜索中...';
            results.innerHTML = '';
            
            try {
                const params = new URLSearchParams();
                if (searchTerm) params.append('search', searchTerm);
                if (category) params.append('category', category);
                params.append('limit', '50');
                
                const response = await fetch(`/api/firebase/products?${params}`);
                const data = await response.json();
                
                if (data.success) {
                    firebaseProducts = data.products;
                    renderFirebaseProducts(data.products);
                    status.innerHTML = `✅ 找到 ${data.count} 个商品`;
                } else {
                    status.innerHTML = '❌ 搜索失败';
                }
            } catch (error) {
                status.innerHTML = '❌ 网络错误';
                console.error(error);
            }
        }
        
        async function loadAllFirebaseProducts() {
            const status = document.getElementById('firebaseStatus');
            status.innerHTML = '📋 加载中...';
            
            try {
                const response = await fetch('/api/firebase/products?limit=100');
                const data = await response.json();
                
                if (data.success) {
                    firebaseProducts = data.products;
                    renderFirebaseProducts(data.products);
                    status.innerHTML = `✅ 加载了 ${data.count} 个商品`;
                }
            } catch (error) {
                status.innerHTML = '❌ 加载失败';
                console.error(error);
            }
        }
        
        function renderFirebaseProducts(products) {
            const results = document.getElementById('firebaseResults');
            
            if (products.length === 0) {
                results.innerHTML = '<p class="muted">没有找到商品</p>';
                return;
            }
            
            const html = products.map(product => `
                <div class="card" style="margin-bottom: 15px;">
                    <div class="grid-2">
                        <div>
                            <h4>${product.name}</h4>
                            <p class="muted">SKU: ${product.sku || 'N/A'} | 价格: $${product.price}</p>
                            <p class="muted">分类: ${product.category || '未分类'} | 库存: ${product.stock_quantity || 0}</p>
                            ${product.description ? `<p class="muted">${product.description}</p>` : ''}
                        </div>
                        <div style="text-align: right;">
                            ${product.imageUrl ? `<img src="${product.imageUrl}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;" alt="${product.name}">` : '<div style="width: 80px; height: 80px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999;">无图片</div>'}
                            <div style="margin-top: 10px;">
                                <button class="btn secondary" onclick="editFirebaseProduct('${product.id}')">编辑</button>
                                <button class="btn secondary" onclick="deleteFirebaseProduct('${product.id}')">删除</button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
            
            results.innerHTML = html;
        }
        
        async function createFirebaseProduct(event) {
            event.preventDefault();
            const status = document.getElementById('firebaseCreateStatus');
            
            const formData = new FormData();
            formData.append('name', document.getElementById('firebaseName').value);
            formData.append('price', document.getElementById('firebasePrice').value);
            formData.append('sku', document.getElementById('firebaseSku').value);
            formData.append('code', document.getElementById('firebaseCode').value);
            formData.append('category', document.getElementById('firebaseCategoryCreate').value);
            formData.append('stock_quantity', document.getElementById('firebaseStock').value);
            formData.append('description', document.getElementById('firebaseDescription').value);
            
            const imageFile = document.getElementById('firebaseImage').files[0];
            if (imageFile) {
                formData.append('image', imageFile);
            }
            
            status.innerHTML = '➕ 创建中...';
            
            try {
                const response = await fetch('/api/firebase/products/create-with-image', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    status.innerHTML = '✅ 商品创建成功';
                    document.getElementById('firebaseCreateForm').reset();
                    loadAllFirebaseProducts(); // 刷新列表
                } else {
                    status.innerHTML = `❌ 创建失败: ${data.message || '未知错误'}`;
                }
            } catch (error) {
                status.innerHTML = '❌ 网络错误';
                console.error(error);
            }
        }
        
        async function syncFromClover(overwrite = false) {
            const status = document.getElementById('firebaseSyncStatus');
            const results = document.getElementById('firebaseSyncResults');
            
            status.innerHTML = '🔄 同步中...';
            results.innerHTML = '';
            
            try {
                const response = await fetch(`/api/firebase/sync-clover?overwrite=${overwrite}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    const result = data.result;
                    status.innerHTML = `✅ 同步完成`;
                    results.innerHTML = `
                        <div class="card">
                            <h4>同步结果</h4>
                            <p>✅ 成功同步: ${result.synced} 个商品</p>
                            <p>⏭️ 跳过: ${result.skipped} 个商品</p>
                            <p>❌ 失败: ${result.failed} 个商品</p>
                            ${result.errors.length > 0 ? `<p>错误详情:</p><ul>${result.errors.map(e => `<li>${e.product}: ${e.error}</li>`).join('')}</ul>` : ''}
                        </div>
                    `;
                    loadAllFirebaseProducts(); // 刷新列表
                } else {
                    status.innerHTML = `❌ 同步失败: ${data.message}`;
                }
            } catch (error) {
                status.innerHTML = '❌ 网络错误';
                console.error(error);
            }
        }
        
        async function loadFirebaseStats() {
            const status = document.getElementById('firebaseStatsStatus');
            const results = document.getElementById('firebaseStatsResults');
            
            status.innerHTML = '📊 加载中...';
            results.innerHTML = '';
            
            try {
                const response = await fetch('/api/firebase/statistics');
                const data = await response.json();
                
                if (data.success) {
                    const stats = data.statistics;
                    status.innerHTML = '✅ 统计信息已更新';
                    results.innerHTML = `
                        <div class="grid-2">
                            <div class="card">
                                <h4>📦 商品统计</h4>
                                <p>总商品数: ${stats.total_products}</p>
                                <p>有图片: ${stats.with_image}</p>
                                <p>有描述: ${stats.with_description}</p>
                                <p>完整率: ${stats.completion_rate}%</p>
                            </div>
                            <div class="card">
                                <h4>📂 分类统计</h4>
                                <p>总分类数: ${stats.total_categories}</p>
                                <p>总库存: ${stats.total_stock_quantity}</p>
                                <p>库存价值: $${stats.total_inventory_value}</p>
                            </div>
                        </div>
                    `;
                } else {
                    status.innerHTML = '❌ 加载失败';
                }
            } catch (error) {
                status.innerHTML = '❌ 网络错误';
                console.error(error);
            }
        }
        
        async function exportFirebaseData() {
            try {
                const response = await fetch('/api/firebase/products?limit=1000');
                const data = await response.json();
                
                if (data.success) {
                    const blob = new Blob([JSON.stringify(data.products, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `firebase_products_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                }
            } catch (error) {
                console.error('导出失败:', error);
            }
        }
        
        async function editFirebaseProduct(productId) {
            // TODO: 实现编辑功能
            alert('编辑功能待实现');
        }
        
        async function deleteFirebaseProduct(productId) {
            if (!confirm('确定要删除这个商品吗？')) return;
            
            try {
                const response = await fetch(`/api/firebase/products/${productId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    loadAllFirebaseProducts(); // 刷新列表
                } else {
                    alert('删除失败');
                }
            } catch (error) {
                console.error('删除失败:', error);
                alert('删除失败');
            }
        }
    </script>
</body>
</html>'''

app = FastAPI(title="StockWise", version="2.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://easternmarket.ca",
        "https://www.easternmarket.ca",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include Firebase router if available
if FIREBASE_ENABLED and firebase_router:
    app.include_router(firebase_router)
    logging.info("Firebase API endpoints enabled")

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

# Startup env var check — visible immediately in Cloud Run logs
logging.basicConfig(level=logging.INFO)
_startup_logger = logging.getLogger("startup")
_startup_logger.info("=== StockWise startup env check ===")
_startup_logger.info("CLOVER_API_KEY present: %s", bool(os.environ.get("CLOVER_API_KEY")))
_startup_logger.info("MERCHANT_ID present:    %s", bool(os.environ.get("MERCHANT_ID")))
_startup_logger.info("ANTHROPIC_API_KEY present: %s", bool(os.environ.get("ANTHROPIC_API_KEY")))
_startup_logger.info("GEMINI_API_KEY present:    %s", bool(os.environ.get("GEMINI_API_KEY")))
_startup_logger.info("FIREBASE_ENABLED: %s", FIREBASE_ENABLED)
if FIREBASE_ENABLED:
    _startup_logger.info("FIREBASE_SERVICE_ACCOUNT_PATH present: %s", bool(os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")))
    _startup_logger.info("FIREBASE_SERVICE_ACCOUNT_JSON present: %s", bool(os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")))
    _startup_logger.info("FIREBASE_STORAGE_BUCKET: %s", os.environ.get("FIREBASE_STORAGE_BUCKET", "stockwise-486801.appspot.com"))
if not os.environ.get("CLOVER_API_KEY") or not os.environ.get("MERCHANT_ID"):
    _startup_logger.error(
        "MISSING REQUIRED ENV VARS: CLOVER_API_KEY and/or MERCHANT_ID not set. "
        "All product/sales API calls will fail. "
        "Set them via gcloud run deploy --set-env-vars or Cloud Run console."
    )
_startup_logger.info("===================================")


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
    # 优先使用Anthropic (从Secret Manager获取)
    anthropic_key = get_anthropic_api_key().strip()
    if anthropic_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
            logger.info("Anthropic AI client initialized with secure configuration")
            return client, "anthropic", ""
        except Exception as exc:
            logger.exception("Anthropic client init failed")
            return None, "", str(exc)
    
    # 回退到Gemini (从Secret Manager获取)
    gemini_key = get_gemini_api_key().strip()
    if gemini_key:
        if genai is None:
            return None, "", "google-genai 依赖未安装"
        try:
            genai.configure(api_key=gemini_key)
            logger.info("Gemini AI client initialized with secure configuration")
            return genai, "gemini", ""
        except Exception as exc:
            logger.exception("Gemini client init failed")
            return None, "", str(exc)
    
    return None, "", "AI API keys not configured in Secret Manager"


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
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
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
    prompt = f'''你是北美华人超市（Eastern Market，加拿大萨斯喀彻温省）的商品分类专家。
请结合中式烹饪习惯和华人饮食文化，对以下商品进行分类，返回严格 JSON：
{{
  "main_category": "主类别（如蔬果、肉类、海鲜、干货调料、冷冻食品、熟食卤味、饮料零食、日用品等）",
  "sub_category": "子类别",
  "attributes": ["属性1", "属性2"],
  "target_customers": ["华人家庭"],
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
    prompt = f'''你是北美华人超市（Eastern Market，加拿大萨斯喀彻温省）的商品营销文案专家。
请结合华人饮食文化和中式烹饪习惯，为以下商品生成吸引华人顾客的营销描述，返回严格 JSON：
{{
  "description": "商品描述（融入中式烹饪使用场景）",
  "keywords": ["关键词1", "关键词2"],
  "selling_points": ["卖点1", "卖点2"],
  "usage_suggestions": "中式烹饪用法建议",
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


# ============================================================================
# NEW ENDPOINTS - Product Management & Enhanced AI Features
# ============================================================================

@app.get("/api/products/managed")
async def get_managed_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    has_description: Optional[bool] = Query(None)
):
    """Get all managed products with filters"""
    try:
        pm = get_product_manager()
        filters = {}
        if search:
            filters["search"] = search
        if category:
            filters["category"] = category
        if has_description is not None:
            filters["has_description"] = has_description
        
        products = pm.get_all_products(filters)
        stats = pm.get_statistics()
        
        return {
            "products": products,
            "count": len(products),
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/save")
async def save_product(payload: Dict):
    """Save or update product information"""
    try:
        pm = get_product_manager()
        product = pm.save_product(payload)
        return {
            "success": True,
            "product": product,
            "message": "Product saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/products/{product_key}/field")
async def update_product_field(product_key: str, payload: Dict):
    """Update a specific field of a product"""
    try:
        field = payload.get("field")
        value = payload.get("value")
        
        if not field:
            raise HTTPException(status_code=400, detail="Field name is required")
        
        pm = get_product_manager()
        product = pm.update_product_field(product_key, field, value)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "product": product,
            "message": f"Field '{field}' updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/bulk-update")
async def bulk_update_products(payload: Dict):
    """Bulk update multiple products"""
    try:
        updates = payload.get("updates", [])
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        pm = get_product_manager()
        result = pm.bulk_update(updates)
        
        return {
            "success": True,
            "result": result,
            "message": f"Bulk update completed: {result['success_count']} succeeded, {result['failed_count']} failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/export")
async def export_products(format: str = Query("json", pattern="^(json|csv)$")):
    """Export all products for external website integration"""
    try:
        pm = get_product_manager()
        export_data = pm.export_products(format)
        
        if format == "csv":
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=products_export.csv"}
            )
        else:
            return {
                "format": format,
                "data": export_data,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-results")
async def get_ai_results(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    has_classification: Optional[bool] = Query(None),
    has_description: Optional[bool] = Query(None),
    has_recipe: Optional[bool] = Query(None),
    has_image: Optional[bool] = Query(None)
):
    """Get all AI processing results with filters"""
    try:
        store = get_ai_results_store()
        filters = {}
        if search:
            filters["search"] = search
        if category:
            filters["category"] = category
        if has_classification is not None:
            filters["has_classification"] = has_classification
        if has_description is not None:
            filters["has_description"] = has_description
        if has_recipe is not None:
            filters["has_recipe"] = has_recipe
        if has_image is not None:
            filters["has_image"] = has_image
        
        results = store.get_all_results(filters)
        stats = store.get_statistics()
        
        return {
            "results": results,
            "count": len(results),
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai-results/save-classification")
async def save_ai_classification(payload: Dict):
    """Save AI classification result to backend storage"""
    try:
        product_info = payload.get("product_info", {})
        classification = payload.get("classification", {})
        
        if not product_info or not classification:
            raise HTTPException(status_code=400, detail="product_info and classification are required")
        
        store = get_ai_results_store()
        result = store.save_classification(product_info, classification)
        
        return {
            "success": True,
            "result": result,
            "message": "Classification saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai-results/save-description")
async def save_ai_description(payload: Dict):
    """Save AI description result to backend storage"""
    try:
        product_info = payload.get("product_info", {})
        description = payload.get("description", {})
        
        if not product_info or not description:
            raise HTTPException(status_code=400, detail="product_info and description are required")
        
        store = get_ai_results_store()
        result = store.save_description(product_info, description)
        
        return {
            "success": True,
            "result": result,
            "message": "Description saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/ai-results/{product_key}/edit")
async def edit_ai_result(product_key: str, payload: Dict):
    """Edit a specific field in an AI result"""
    try:
        result_type = payload.get("result_type")
        field = payload.get("field")
        value = payload.get("value")
        
        if not result_type or not field:
            raise HTTPException(status_code=400, detail="result_type and field are required")
        
        if result_type not in ["classification", "description", "recipe", "image_info"]:
            raise HTTPException(status_code=400, detail="Invalid result_type")
        
        store = get_ai_results_store()
        result = store.update_result_field(product_key, result_type, field, value)
        
        if not result:
            raise HTTPException(status_code=404, detail="AI result not found")
        
        return {
            "success": True,
            "result": result,
            "message": f"Field '{field}' in '{result_type}' updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-results/export")
async def export_ai_results(
    format: str = Query("json", pattern="^(json|csv)$"),
    result_types: Optional[str] = Query(None)
):
    """Export AI results for external website integration"""
    try:
        store = get_ai_results_store()
        types_list = result_types.split(",") if result_types else None
        export_data = store.export_results(format, types_list)
        
        if format == "csv":
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=ai_results_export.csv"}
            )
        else:
            return {
                "format": format,
                "data": export_data,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/recipe")
async def generate_recipe(payload: Dict):
    """Generate recipe recommendation for a product"""
    try:
        product_info = payload.get("product_info", {})
        recipe_type = payload.get("recipe_type", "simple")
        
        if not product_info or not product_info.get("name"):
            raise HTTPException(status_code=400, detail="product_info with name is required")
        
        engine = get_ai_enhancements_engine()
        recipe = engine.generate_recipe(product_info, recipe_type)
        
        # Save to AI results store
        store = get_ai_results_store()
        store.save_recipe(product_info, recipe)
        
        return {
            "success": True,
            "recipe": recipe,
            "message": "Recipe generated and saved successfully"
        }
    except Exception as e:
        logger.error(f"Recipe generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/image-prompt")
async def generate_image_prompt(payload: Dict):
    """Generate image prompt for product visualization"""
    try:
        product_info = payload.get("product_info", {})
        style = payload.get("style", "realistic")
        
        if not product_info or not product_info.get("name"):
            raise HTTPException(status_code=400, detail="product_info with name is required")
        
        engine = get_ai_enhancements_engine()
        image_prompt = engine.generate_image_prompt(product_info, style)
        
        # Save to AI results store
        store = get_ai_results_store()
        store.save_image_info(product_info, image_prompt)
        
        return {
            "success": True,
            "image_prompt": image_prompt,
            "message": "Image prompt generated and saved successfully"
        }
    except Exception as e:
        logger.error(f"Image prompt generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/batch-recipe")
async def batch_generate_recipes(payload: Dict):
    """Batch generate recipes for multiple products"""
    try:
        products = payload.get("products", [])
        recipe_type = payload.get("recipe_type", "simple")
        
        if not products:
            raise HTTPException(status_code=400, detail="No products provided")
        
        engine = get_ai_enhancements_engine()
        result = engine.batch_generate_recipes(products, recipe_type)
        
        # Save successful results to store
        store = get_ai_results_store()
        for item in result["results"]:
            if item["success"]:
                store.save_recipe(item["product"], item["recipe"])
        
        return {
            "success": True,
            "result": result,
            "message": f"Batch recipe generation completed: {result['success_count']} succeeded, {result['failed_count']} failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/batch-image-prompt")
async def batch_generate_image_prompts(payload: Dict):
    """Batch generate image prompts for multiple products"""
    try:
        products = payload.get("products", [])
        style = payload.get("style", "realistic")
        
        if not products:
            raise HTTPException(status_code=400, detail="No products provided")
        
        engine = get_ai_enhancements_engine()
        result = engine.batch_generate_image_prompts(products, style)
        
        # Save successful results to store
        store = get_ai_results_store()
        for item in result["results"]:
            if item["success"]:
                store.save_image_info(item["product"], item["image_prompt"])
        
        return {
            "success": True,
            "result": result,
            "message": f"Batch image prompt generation completed: {result['success_count']} succeeded, {result['failed_count']} failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/merged")
async def get_products_with_ai_results():
    """Get products merged with AI results for complete data export"""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="No products found")
        
        store = get_ai_results_store()
        merged = store.merge_with_products(inventory)
        
        return {
            "products": merged,
            "count": len(merged),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CATALOG MANAGEMENT - Local edits storage (keyed by Clover product ID)
# =============================================================================

CATALOG_EDITS_FILE = os.path.join("data", "catalog_edits.json")


def _load_catalog_edits() -> dict:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(CATALOG_EDITS_FILE):
        return {}
    try:
        with open(CATALOG_EDITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_catalog_edits(edits: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(CATALOG_EDITS_FILE, "w", encoding="utf-8") as f:
        json.dump(edits, f, ensure_ascii=False, indent=2)


def _build_catalog_product(clover_item: dict, local_edits: dict, ai_result: dict) -> dict:
    """Merge a Clover inventory item with local edits and AI results into one catalog record."""
    raw_price = clover_item.get("price", 0)
    p: dict = {
        "id": clover_item.get("id", ""),
        "name": clover_item.get("name", ""),
        "price": raw_price / 100 if isinstance(raw_price, int) and raw_price > 100 else raw_price,
        "sku": clover_item.get("sku", ""),
        "code": clover_item.get("code", ""),
        "alt_code": clover_item.get("alt_code", ""),
    }
    if local_edits:
        for field in [
            "display_name", "price_note", "category", "subcategory", "brand", "origin",
            "unit", "weight_spec", "status", "featured", "tags", "notes",
            "image_url", "image_gallery", "description", "long_description",
            "keywords", "selling_points", "allergens", "shelf_life", "storage", "nutrition",
        ]:
            if field in local_edits:
                p[field] = local_edits[field]
    if ai_result:
        if ai_result.get("classification"):
            p["ai_classification"] = ai_result["classification"]
        if ai_result.get("description"):
            p["ai_description"] = ai_result["description"]
        if ai_result.get("recipe"):
            p["ai_recipe"] = ai_result["recipe"]
        if ai_result.get("image_info"):
            p["ai_image"] = ai_result["image_info"]
    # Apply local AI edits (override stored AI results with user corrections)
    if local_edits:
        if local_edits.get("ai_classification_edit"):
            p["ai_classification"] = {**(p.get("ai_classification") or {}), **local_edits["ai_classification_edit"]}
        if local_edits.get("ai_description_edit"):
            p["ai_description"] = {**(p.get("ai_description") or {}), **local_edits["ai_description_edit"]}
    return p


def _find_ai_result_for_id(ai_results: list, clover_id: str) -> Optional[dict]:
    for ar in ai_results:
        pi = ar.get("product_info") or {}
        if pi.get("id") == clover_id or pi.get("clover_id") == clover_id:
            return ar
    return None


@app.get("/api/products/catalog")
async def get_products_catalog():
    """Fetch full product catalog: Clover inventory + local edits + AI results."""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory()
        if not inventory:
            return {"products": [], "count": 0, "categories": [], "timestamp": datetime.now().isoformat()}

        local_edits = _load_catalog_edits()
        store = get_ai_results_store()
        ai_results = store.get_all_results({})

        catalog = []
        for item in inventory:
            cid = item.get("id", "")
            ai_res = _find_ai_result_for_id(ai_results, cid)
            catalog.append(_build_catalog_product(item, local_edits.get(cid), ai_res))

        categories = sorted({
            p.get("category") or (p.get("ai_classification") or {}).get("main_category", "")
            for p in catalog
            if p.get("category") or (p.get("ai_classification") or {}).get("main_category")
        })

        return {
            "products": catalog,
            "count": len(catalog),
            "categories": [c for c in categories if c],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products/{product_id}/update")
async def update_product_local(product_id: str, payload: Dict):
    """Save product field edits locally. Does NOT write anything to Clover POS."""
    try:
        edits = _load_catalog_edits()
        record = edits.get(product_id, {})

        # Editable product fields to persist
        editable = [
            "display_name", "price_note", "category", "subcategory", "brand", "origin",
            "unit", "weight_spec", "status", "featured", "tags", "notes",
            "image_url", "image_gallery", "description", "long_description",
            "keywords", "selling_points", "allergens", "shelf_life", "storage", "nutrition",
        ]
        for field in editable:
            if field in payload:
                record[field] = payload[field]
        # Store AI field edits (merged with AI results in _build_catalog_product)
        if payload.get("ai_classification_edit"):
            record["ai_classification_edit"] = payload["ai_classification_edit"]
        if payload.get("ai_description_edit"):
            record["ai_description_edit"] = payload["ai_description_edit"]
        record["updated_at"] = datetime.now().isoformat()
        edits[product_id] = record
        _save_catalog_edits(edits)

        return {
            "success": True,
            "product": record,
            "message": "Saved locally. NOT written to Clover POS.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PUBLIC API - For supermarket website (no authentication required)
# =============================================================================

@app.get("/api/public/products")
async def public_get_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Public product catalog API for supermarket website. No authentication required."""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory() or []
        local_edits = _load_catalog_edits()
        store = get_ai_results_store()
        ai_results = store.get_all_results({})

        catalog = []
        for item in inventory:
            cid = item.get("id", "")
            p = _build_catalog_product(item, local_edits.get(cid), _find_ai_result_for_id(ai_results, cid))

            if search:
                q = search.lower()
                name_match = q in (p.get("display_name") or p.get("name") or "").lower()
                sku_match = q in (p.get("sku") or "").lower()
                desc_match = q in (p.get("description") or "").lower()
                if not (name_match or sku_match or desc_match):
                    continue
            if category:
                pcat = (p.get("category") or (p.get("ai_classification") or {}).get("main_category") or "").lower()
                if pcat != category.lower():
                    continue
            if featured is not None and bool(p.get("featured")) != featured:
                continue
            catalog.append(p)

        return {
            "products": catalog[offset: offset + limit],
            "total": len(catalog),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/public/products/{product_id}")
async def public_get_product(product_id: str):
    """Get a single product's full detail including AI data (public, no auth required)."""
    try:
        api = get_api_handler()
        inventory = api.fetch_full_inventory() or []
        item = next((i for i in inventory if i.get("id") == product_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")

        local_edits = _load_catalog_edits()
        store = get_ai_results_store()
        ai_results = store.get_all_results({})
        p = _build_catalog_product(item, local_edits.get(product_id), _find_ai_result_for_id(ai_results, product_id))

        return {"product": p, "timestamp": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
