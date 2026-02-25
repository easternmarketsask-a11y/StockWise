import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

class InventoryAlert:
    def __init__(self, api_handler):
        self.api = api_handler
        self.low_stock_threshold = 10  # 低库存阈值
        self.out_of_stock_threshold = 0  # 缺货阈值
        
    def check_inventory_status(self, inventory):
        """检查库存状态"""
        if not inventory:
            return pd.DataFrame()
            
        alerts = []
        for item in inventory:
            # 获取最近30天销量作为参考
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            
            recent_sales = self.api.fetch_targeted_sales([item['id']], start_ts, end_ts)
            monthly_sales = sum(s.get('unitQty', 0) for s in recent_sales) / 1000 if recent_sales else 0
            
            # 计算库存状态
            stock_level = self._estimate_stock_level(item, monthly_sales)
            alert_type = self._determine_alert_type(stock_level, monthly_sales)
            
            if alert_type != 'normal':
                alerts.append({
                    '商品信息': item['name'],
                    'SKU': item.get('sku', '-'),
                    'Product Code': item.get('code', '-'),
                    '当前库存': stock_level,
                    '月销量': round(monthly_sales, 2),
                    '预警类型': alert_type,
                    '建议': self._generate_suggestion(alert_type, monthly_sales)
                })
        
        return pd.DataFrame(alerts)
    
    def _estimate_stock_level(self, item, monthly_sales):
        """估算库存水平（简化版本）"""
        # 这里可以根据实际业务逻辑调整
        # 目前使用月销量作为参考指标
        return monthly_sales
    
    def _determine_alert_type(self, stock_level, monthly_sales):
        """确定预警类型"""
        if monthly_sales == 0:
            return 'no_sales'
        elif stock_level < self.out_of_stock_threshold:
            return 'out_of_stock'
        elif stock_level < self.low_stock_threshold:
            return 'low_stock'
        else:
            return 'normal'
    
    def _generate_suggestion(self, alert_type, monthly_sales):
        """生成建议"""
        suggestions = {
            'no_sales': "考虑促销或下架",
            'out_of_stock': "立即补货",
            'low_stock': "建议尽快补货",
            'normal': "库存正常"
        }
        return suggestions.get(alert_type, "关注库存变化")
    
    def render_alert_dashboard(self, inventory):
        """渲染预警仪表板"""
        st.markdown("### 📊 库存预警监控")
        
        alerts_df = self.check_inventory_status(inventory)
        
        if alerts_df.empty:
            st.success("✅ 所有商品库存状态正常")
            return
        
        # 统计预警类型
        alert_counts = alerts_df['预警类型'].value_counts()
        
        # 显示预警统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("缺货", alert_counts.get('out_of_stock', 0), delta_color="inverse")
        
        with col2:
            st.metric("低库存", alert_counts.get('low_stock', 0), delta_color="inverse")
        
        with col3:
            st.metric("无销量", alert_counts.get('no_sales', 0))
        
        with col4:
            st.metric("需关注", len(alerts_df), delta_color="inverse")
        
        # 显示详细预警列表
        st.markdown("#### 🚨 详细预警信息")
        
        # 按预警类型排序显示
        priority_order = ['out_of_stock', 'low_stock', 'no_sales']
        alerts_df['优先级'] = alerts_df['预警类型'].map({t: i for i, t in enumerate(priority_order)})
        alerts_df = alerts_df.sort_values('优先级')
        
        # 添加颜色标识
        def highlight_alert(row):
            if row['预警类型'] == 'out_of_stock':
                return ['background-color: #ffebee'] * len(row)
            elif row['预警类型'] == 'low_stock':
                return ['background-color: #fff3e0'] * len(row)
            elif row['预警类型'] == 'no_sales':
                return ['background-color: #f3e5f5'] * len(row)
            return [''] * len(row)
        
        styled_df = alerts_df.drop('优先级', axis=1).style.apply(highlight_alert, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # 导出预警报告
        if st.button("📥 导出预警报告"):
            csv = alerts_df.drop('优先级', axis=1).to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "💾 下载预警报告.csv",
                csv,
                f"Inventory_Alerts_{datetime.now().strftime('%m%d')}.csv",
                "text/csv"
            )
