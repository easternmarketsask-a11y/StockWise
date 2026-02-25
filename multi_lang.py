import streamlit as st

class MultiLanguage:
    def __init__(self):
        self.translations = {
            'zh': {
                'app_title': 'StockWise | EasternMarket',
                'login_title': '🔐 StockWise 访问验证',
                'password_prompt': '请输入访问密码:',
                'login_button': '登录',
                'password_error': '密码错误，请重试。',
                'system_ready': '系统就绪: 已同步 {count} 件商品',
                'no_products': '店铺中暂无商品数据',
                'search_title': '🔍 销量分析查询',
                'start_date': '开始日期',
                'end_date': '结束日期',
                'search_placeholder': '输入名称或条码片段...',
                'search_button': '查询',
                'auditing': '深度审计中...',
                'total_sales': '汇总销量 (Qty/Lbs)',
                'no_sales_record': '该期间内无销量记录。',
                'product_not_found': '找不到包含 \'{query}\' 的商品。',
                'report_tools': '📦 报表工具',
                'export_button': '导出近30天全店销售产品 CSV',
                'syncing': '同步全店流水中...',
                'export_download': '💾 点击下载报表.csv',
                'logout': '🚪 退出登录',
                'inventory_alerts': '📊 库存预警监控',
                'trend_analysis': '📈 销售趋势分析',
                'data_visualization': '📊 数据可视化',
                'out_of_stock': '缺货',
                'low_stock': '低库存',
                'no_sales': '无销量',
                'need_attention': '需关注',
                'detailed_alerts': '🚨 详细预警信息',
                'export_alerts': '📥 导出预警报告',
                'download_alerts': '💾 下载预警报告.csv'
            },
            'en': {
                'app_title': 'StockWise | EasternMarket',
                'login_title': '🔐 StockWise Access Verification',
                'password_prompt': 'Please enter access password:',
                'login_button': 'Login',
                'password_error': 'Password incorrect, please try again.',
                'system_ready': 'System Ready: {count} products synchronized',
                'no_products': 'No product data in the store',
                'search_title': '🔍 Sales Analysis Query',
                'start_date': 'Start Date',
                'end_date': 'End Date',
                'search_placeholder': 'Enter name or barcode fragment...',
                'search_button': 'Search',
                'auditing': 'Deep auditing...',
                'total_sales': 'Total Sales (Qty/Lbs)',
                'no_sales_record': 'No sales records in this period.',
                'product_not_found': 'Product containing \'{query}\' not found.',
                'report_tools': '📦 Report Tools',
                'export_button': 'Export Last 30 Days Store Sales CSV',
                'syncing': 'Syncing store transactions...',
                'export_download': '💾 Click to download report.csv',
                'logout': '🚪 Logout',
                'inventory_alerts': '📊 Inventory Alert Monitor',
                'trend_analysis': '📈 Sales Trend Analysis',
                'data_visualization': '📊 Data Visualization',
                'out_of_stock': 'Out of Stock',
                'low_stock': 'Low Stock',
                'no_sales': 'No Sales',
                'need_attention': 'Need Attention',
                'detailed_alerts': '🚨 Detailed Alert Information',
                'export_alerts': '📥 Export Alert Report',
                'download_alerts': '💾 Download alert_report.csv'
            }
        }
    
    def get_text(self, key, **kwargs):
        """获取翻译文本"""
        lang = st.session_state.get('language', 'zh')
        text = self.translations[lang].get(key, key)
        return text.format(**kwargs) if kwargs else text
    
    def render_language_selector(self):
        """渲染语言选择器"""
        if 'language' not in st.session_state:
            st.session_state.language = 'zh'
        
        col1, col2 = st.columns([4, 1])
        with col2:
            lang = st.selectbox(
                'Language/语言',
                ['中文', 'English'],
                index=0 if st.session_state.language == 'zh' else 1,
                key='lang_selector'
            )
            st.session_state.language = 'zh' if lang == '中文' else 'en'
