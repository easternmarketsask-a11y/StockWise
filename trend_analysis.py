import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

class TrendAnalysis:
    def __init__(self, api_handler):
        self.api = api_handler
    
    def compare_periods(self, item_ids, current_start, current_end, comparison_type='mom'):
        """比较不同时期的销售数据"""
        if comparison_type == 'mom':  # 月环比
            prev_start = current_start - timedelta(days=30)
            prev_end = current_start - timedelta(days=1)
        elif comparison_type == 'yoy':  # 年同比
            prev_start = current_start - timedelta(days=365)
            prev_end = current_end - timedelta(days=365)
        else:
            return None
        
        # 获取两个时期的数据
        current_sales = self.api.fetch_targeted_sales(item_ids, int(current_start.timestamp() * 1000), int(current_end.timestamp() * 1000))
        previous_sales = self.api.fetch_targeted_sales(item_ids, int(prev_start.timestamp() * 1000), int(prev_end.timestamp() * 1000))
        
        return {
            'current': self._summarize_sales(current_sales),
            'previous': self._summarize_sales(previous_sales),
            'period_type': comparison_type
        }
    
    def _summarize_sales(self, sales_data):
        """汇总销售数据"""
        if not sales_data:
            return {'quantity': 0, 'revenue': 0, 'orders': 0}
        
        quantity = sum(s.get('unitQty', 0) for s in sales_data) / 1000
        revenue = sum(s.get('price', 0) for s in sales_data) / 100
        orders = len(set(s.get('orderId') for s in sales_data if s.get('orderId')))
        
        return {
            'quantity': quantity,
            'revenue': revenue,
            'orders': orders
        }
    
    def calculate_growth_rates(self, comparison_data):
        """计算增长率"""
        if not comparison_data:
            return pd.DataFrame()
        
        current = comparison_data['current']
        previous = comparison_data['previous']
        period_type = comparison_data['period_type']
        
        def calc_rate(current_val, prev_val):
            if prev_val == 0:
                return 0 if current_val == 0 else float('inf')
            return ((current_val - prev_val) / prev_val) * 100
        
        growth_data = {
            '指标': ['销量', '销售额', '订单数'],
            '本期': [
                round(current['quantity'], 2),
                f"${current['revenue']:.2f}",
                current['orders']
            ],
            '上期': [
                round(previous['quantity'], 2),
                f"${previous['revenue']:.2f}",
                previous['orders']
            ],
            '增长率(%)': [
                calc_rate(current['quantity'], previous['quantity']),
                calc_rate(current['revenue'], previous['revenue']),
                calc_rate(current['orders'], previous['orders'])
            ]
        }
        
        df = pd.DataFrame(growth_data)
        
        # 格式化增长率显示
        def format_growth(rate):
            if rate == float('inf'):
                return "📈 +∞%"
            elif rate > 0:
                return f"📈 +{rate:.1f}%"
            elif rate < 0:
                return f"📉 {rate:.1f}%"
            else:
                return "➡️ 0%"
        
        df['增长率(%)'] = df['增长率(%)'].apply(format_growth)
        
        return df
    
    def analyze_trend_direction(self, item_ids, days=30):
        """分析趋势方向"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sales_data = self.api.fetch_targeted_sales(
            item_ids, 
            int(start_date.timestamp() * 1000), 
            int(end_date.timestamp() * 1000)
        )
        
        if not sales_data:
            return "无足够数据进行分析"
        
        # 按天分组数据
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['createdTime'], unit='ms').dt.date
        
        daily_sales = df.groupby('date').agg({
            'price': 'sum',
            'unitQty': 'sum'
        }).reset_index()
        
        daily_sales['revenue'] = daily_sales['price'] / 100
        daily_sales['quantity'] = daily_sales['unitQty'] / 1000
        
        if len(daily_sales) < 7:
            return "数据不足，建议至少7天数据"
        
        # 计算趋势
        x = np.arange(len(daily_sales))
        revenue_slope = np.polyfit(x, daily_sales['revenue'], 1)[0]
        quantity_slope = np.polyfit(x, daily_sales['quantity'], 1)[0]
        
        # 判断趋势
        if revenue_slope > 0.1 and quantity_slope > 0.01:
            return "📈 强劲上升趋势"
        elif revenue_slope > 0 and quantity_slope > 0:
            return "📊 温和上升趋势"
        elif revenue_slope < -0.1 and quantity_slope < -0.01:
            return "📉 明显下降趋势"
        elif revenue_slope < 0 and quantity_slope < 0:
            return "➡️ 平缓下降趋势"
        else:
            return "➡️ 波动稳定"
    
    def render_trend_dashboard(self, inventory, query=None):
        """渲染趋势分析仪表板"""
        st.markdown("### 📈 销售趋势分析")
        
        if not inventory:
            st.warning("请先加载商品数据")
            return
        
        # 时期选择
        col1, col2 = st.columns(2)
        with col1:
            analysis_type = st.selectbox("分析类型", ["月环比", "年同比"])
        with col2:
            date_range = st.date_input("选择分析期间", value=[
                datetime.now() - timedelta(days=30),
                datetime.now()
            ])
        
        if len(date_range) != 2:
            st.warning("请选择完整的日期范围")
            return
        
        start_date, end_date = date_range
        
        # 商品选择
        if query:
            matched_items = [i for i in inventory if query.lower() in str(i.get('name') or "").lower()]
        else:
            matched_items = inventory[:10]  # 默认分析前10个商品
        
        if not matched_items:
            st.warning("未找到匹配的商品")
            return
        
        # 执行趋势分析
        with st.spinner("分析趋势中..."):
            comparison_type = 'mom' if analysis_type == "月环比" else 'yoy'
            comparison_data = self.compare_periods(
                [item['id'] for item in matched_items],
                start_date,
                end_date,
                comparison_type
            )
            
            if comparison_data:
                # 显示增长率表格
                growth_df = self.calculate_growth_rates(comparison_data)
                st.markdown("#### 📊 增长率对比")
                st.dataframe(growth_df, use_container_width=True)
                
                # 趋势方向分析
                trend_direction = self.analyze_trend_direction(
                    [item['id'] for item in matched_items],
                    days=(end_date - start_date).days
                )
                st.markdown(f"#### 🧭 趋势判断")
                st.info(trend_direction)
                
                # 详细对比
                current = comparison_data['current']
                previous = comparison_data['previous']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "本期销量",
                        f"{current['quantity']:.2f}",
                        delta=f"{current['quantity'] - previous['quantity']:.2f}",
                        delta_color="normal" if current['quantity'] >= previous['quantity'] else "inverse"
                    )
                
                with col2:
                    st.metric(
                        "本期销售额",
                        f"${current['revenue']:.2f}",
                        delta=f"${current['revenue'] - previous['revenue']:.2f}",
                        delta_color="normal" if current['revenue'] >= previous['revenue'] else "inverse"
                    )
            else:
                st.error("趋势分析失败，请检查数据")
