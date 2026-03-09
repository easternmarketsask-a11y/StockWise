import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ChartEngine:
    @staticmethod
    def create_sales_trend_chart(df, title='销售趋势图'):
        if df.empty:
            return None

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df['商品信息'],
                y=df['区间销量'],
                name='销量',
                marker_color='#1E88E5',
                yaxis='y',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df['商品信息'],
                y=df['销售总额'].str.replace('$', '').astype(float),
                name='销售额',
                mode='lines+markers',
                line=dict(color='#FF6B6B', width=3),
                yaxis='y2',
            )
        )
        fig.update_layout(
            title=title,
            xaxis_title='商品',
            yaxis=dict(title='销量', side='left'),
            yaxis2=dict(title='销售额 ($)', side='right', overlaying='y'),
            legend=dict(x=0.01, y=0.99),
            template='plotly_white',
            height=400,
        )
        return fig

    @staticmethod
    def create_top_products_chart(df, top_n=10):
        if df.empty:
            return None

        top_df = df.nlargest(top_n, '区间销量')
        fig = px.bar(
            top_df,
            x='区间销量',
            y='商品信息',
            orientation='h',
            title=f'热销商品 TOP {top_n}',
            color='区间销量',
            color_continuous_scale='Blues',
        )
        fig.update_layout(
            xaxis_title='销量',
            yaxis_title='商品',
            height=max(400, top_n * 40),
            yaxis={'categoryorder': 'total ascending'},
        )
        return fig

    @staticmethod
    def create_revenue_pie_chart(df):
        if df.empty:
            return None

        df_copy = df.copy()
        df_copy['销售总额数值'] = df_copy['销售总额'].str.replace('$', '').astype(float)
        df_sorted = df_copy.sort_values('销售总额数值', ascending=False)
        threshold = 0.05
        main_items = df_sorted[df_sorted['销售总额数值'] >= df_sorted['销售总额数值'].sum() * threshold]
        other_total = df_sorted[df_sorted['销售总额数值'] < df_sorted['销售总额数值'].sum() * threshold]['销售总额数值'].sum()
        chart_data = pd.concat(
            [
                main_items[['商品信息', '销售总额数值']],
                pd.DataFrame([{'商品信息': '其他', '销售总额数值': other_total}]),
            ]
        )
        fig = px.pie(chart_data, values='销售总额数值', names='商品信息', title='销售额占比分布')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        return fig

    @staticmethod
    def create_daily_trend_chart(sales_data):
        if not sales_data:
            return None

        df = pd.DataFrame(sales_data)
        if 'createdTime' not in df.columns:
            return None

        df['date'] = pd.to_datetime(df['createdTime'], unit='ms').dt.date
        daily_sales = df.groupby('date').agg({'price': 'sum', 'unitQty': 'sum'}).reset_index()
        daily_sales['销售额'] = daily_sales['price'] / 100
        daily_sales['销量'] = daily_sales['unitQty'] / 1000

        fig = make_subplots(specs=[[{'secondary_y': True}]])
        fig.add_trace(go.Bar(x=daily_sales['date'], y=daily_sales['销量'], name='销量'), secondary_y=False)
        fig.add_trace(go.Scatter(x=daily_sales['date'], y=daily_sales['销售额'], name='销售额', mode='lines+markers'), secondary_y=True)
        fig.update_xaxes(title_text='日期')
        fig.update_yaxes(title_text='销量', secondary_y=False)
        fig.update_yaxes(title_text='销售额 ($)', secondary_y=True)
        fig.update_layout(title='每日销售趋势', height=400)
        return fig
