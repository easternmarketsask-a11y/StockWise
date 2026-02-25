import streamlit as st
import time, os
from datetime import datetime, timedelta
from api_handler import CloverAPIHandler
from data_engine import DataEngine
from ui_render import UIRenderer
from chart_engine import ChartEngine
from inventory_alert import InventoryAlert
from trend_analysis import TrendAnalysis
from multi_lang import MultiLanguage
from product_ai_manager import ProductAIManager

def main():
    # 多语言支持
    ml = MultiLanguage()
    
    st.set_page_config(page_title=ml.get_text('app_title'), layout="centered")
    
    # 密码验证
    if not st.session_state.get('authenticated', False):
        st.title(ml.get_text('login_title'))
        password = st.text_input(ml.get_text('password_prompt'), type="password")
        if st.button(ml.get_text('login_button')):
            if password == "8089":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error(ml.get_text('password_error'))
        st.stop()
    
    ui, api, engine = UIRenderer(), CloverAPIHandler(), DataEngine()
    chart_engine, alert_system, trend_analyzer = ChartEngine(), InventoryAlert(api), TrendAnalysis(api)
    ai_manager = ProductAIManager(api)
    ui.apply_style()
    
    # 渲染头部和语言选择
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        ui.render_header()
    with header_col2:
        ml.render_language_selector()

    inventory = api.fetch_full_inventory()
    if inventory is None:
        st.error("❌ 商品数据加载失败，请检查API配置和网络连接")
        st.stop()
    elif inventory:
        st.markdown(f"<p style='color: #2E7D32; font-size: 0.8rem; margin-bottom: 10px;'>● {ml.get_text('system_ready', count=len(inventory))}</p>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ {ml.get_text('no_products')}")

    # 功能标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ml.get_text('search_title'), 
        ml.get_text('data_visualization'), 
        ml.get_text('inventory_alerts'), 
        ml.get_text('trend_analysis'),
        "🤖 智能管理"
    ])
    
    with tab1:
        st.markdown(f"### {ml.get_text('search_title')}")
        c1, c2 = st.columns(2)
        with c1: start_date = st.date_input(ml.get_text('start_date'), datetime.now() - timedelta(days=30))
        with c2: end_date = st.date_input(ml.get_text('end_date'), datetime.now())
        query = st.text_input(ml.get_text('search_placeholder'), placeholder=ml.get_text('search_placeholder'))

        if st.button(ml.get_text('search_button'), type="primary"):
            if query:
                with st.spinner(ml.get_text('auditing')):
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
                            st.metric(ml.get_text('total_sales'), f"{df['区间销量'].sum():.2f}")
                            st.table(df)
                            # 保存查询结果用于可视化
                            st.session_state.last_query_df = df
                        else:
                            st.warning(ml.get_text('no_sales_record'))
                    else:
                        st.error(f"❌ {ml.get_text('product_not_found', query=query)}")

        st.markdown("---")
        st.markdown(f"### {ml.get_text('report_tools')}")
        if st.button(ml.get_text('export_button')):
            with st.spinner(ml.get_text('syncing')):
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
                    st.download_button(ml.get_text('export_download'), csv, f"Sales_Summary_{datetime.now().strftime('%m%d')}.csv", "text/csv")
    
    with tab2:
        st.markdown(f"### {ml.get_text('data_visualization')}")
        
        # 获取最近查询的数据用于可视化
        if 'last_query_df' not in st.session_state:
            st.info("请先在销售查询页面进行查询，然后返回此页面查看图表")
        else:
            df = st.session_state.last_query_df
            if not df.empty:
                # 销售趋势图
                fig1 = chart_engine.create_sales_trend_chart(df)
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True)
                
                # 热销商品排行
                fig2 = chart_engine.create_top_products_chart(df)
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True)
                
                # 销售额占比
                fig3 = chart_engine.create_revenue_pie_chart(df)
                if fig3:
                    st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("暂无数据可显示")
    
    with tab3:
        alert_system.render_alert_dashboard(inventory)
    
    with tab4:
        trend_analyzer.render_trend_dashboard(inventory)
    
    with tab5:
        ai_manager.render_ai_dashboard(inventory)
    
    ui.render_custom_footer()

if __name__ == "__main__":
    main()