import streamlit as st
import time, os
from datetime import datetime, timedelta
from api_handler import CloverAPIHandler
from data_engine import DataEngine
from ui_render import UIRenderer

def main():
    st.set_page_config(page_title="StockWise | EasternMarket", layout="centered")
    
    # 密码验证
    if not st.session_state.get('authenticated', False):
        st.title("🔐 StockWise 访问验证")
        password = st.text_input("请输入访问密码:", type="password")
        if st.button("登录"):
            if password == "8089":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误，请重试。")
        st.stop()
    
    ui, api, engine = UIRenderer(), CloverAPIHandler(), DataEngine()
    ui.apply_style()
    ui.render_header()

    inventory = api.fetch_full_inventory()
    if inventory is None:
        st.error("❌ 商品数据加载失败，请检查API配置和网络连接")
        st.stop()
    elif inventory:
        st.markdown(f"<p style='color: #2E7D32; font-size: 0.8rem; margin-bottom: 10px;'>● 系统就绪: 已同步 {len(inventory)} 件商品</p>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ 店铺中暂无商品数据")

    st.markdown("### 🔍 销量分析查询")
    c1, c2 = st.columns(2)
    with c1: start_date = st.date_input("开始日期", datetime.now() - timedelta(days=30))
    with c2: end_date = st.date_input("结束日期", datetime.now())
    query = st.text_input("搜索关键词 (名称/SKU/Code/条码)", placeholder="输入名称或条码片段...")

    if st.button("查询", type="primary"):
        if query:
            with st.spinner("深度审计中..."):
                # 将结束日期对齐到当天的 23:59:59
                s_ts = int(time.mktime(start_date.timetuple()) * 1000)
                e_ts = int(time.mktime((end_date + timedelta(days=1)).timetuple()) * 1000) - 1
                
                matched_items = [i for i in inventory if query.lower() in str(i.get('name') or "").lower() or \
                                 query.lower() in str(i.get('sku') or "").lower() or \
                                 query.lower() in str(i.get('code') or "").lower() or \
                                 query.lower() in str(i.get('alt_code') or "").lower()]
                
                if matched_items:
                    # 抓取数据
                    raw_sales = api.fetch_targeted_sales([m['id'] for m in matched_items], s_ts, e_ts)
                    # 审计数据
                    df = engine.audit_process(query, matched_items, raw_sales)
                    if not df.empty:
                        st.metric("汇总销量 (Qty/Lbs)", f"{df['区间销量'].sum():.2f}")
                        st.table(df)
                    else:
                        st.warning("该期间内无销量记录。")
                else:
                    st.error(f"❌ 找不到包含 '{query}' 的商品。")

    st.markdown("---")
    st.markdown("### 📦 报表工具")
    if st.button("导出近30天全店销售产品 CSV"):
        with st.spinner("同步全店流水中..."):
            # 确保有inventory数据
            if not inventory:
                st.error("商品数据未加载，请刷新页面重试。")
                return
                
            start_30 = datetime.now() - timedelta(days=30)
            s_ts_30 = int(time.mktime(start_30.timetuple()) * 1000)
            e_ts_30 = int(time.mktime(datetime.now().timetuple()) * 1000)
            raw_sales_all = api.fetch_full_period_sales(s_ts_30, e_ts_30)
            if raw_sales_all is None:
                st.error("API请求失败，请检查网络连接和API权限。")
            elif not raw_sales_all:
                st.warning("该时间段内没有销售记录。")
            else:
                export_df = engine.prepare_export_csv(inventory, raw_sales_all)
                csv = export_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("💾 点击下载报表.csv", csv, f"Sales_Summary_{datetime.now().strftime('%m%d')}.csv", "text/csv")
    ui.render_custom_footer()

if __name__ == "__main__":
    main()