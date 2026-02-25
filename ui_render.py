import streamlit as st

class UIRenderer:
    @staticmethod
    def apply_style():
        st.markdown("""
            <style>
            /* 1. 顶部间距：严格保持您设定的 2.5rem，确保 Logo 不被遮挡 */
            .block-container {
                padding-top: 2.5rem !important;
                padding-bottom: 2rem !important;
                max-width: 800px !important;
            }
            
            /* 移动端适配 */
            @media (max-width: 768px) {
                .block-container {
                    padding-top: 1.5rem !important;
                    padding-bottom: 1rem !important;
                    max-width: 95% !important;
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }
                .logo-text {
                    font-size: 1.8rem !important;
                }
                .subtitle {
                    font-size: 0.9rem !important;
                }
                button[kind="primary"], .stDownloadButton button {
                    padding: 0.4rem 1.5rem !important;
                    font-size: 0.9rem !important;
                }
            }
            
            /* 2. 隐藏 Streamlit 默认水印，保持右上角菜单可见 */
            footer {visibility: hidden;}
            header {visibility: visible !important;}
            
            /* 3. 基础配色：明亮背景与 EasternMarket 蓝色 */
            .stApp { background-color: #FFFFFF !important; }
            .logo-text { color: #1E88E5; font-family: sans-serif; font-weight: bold; font-size: 2.3rem; margin-left: 10px; line-height: 1; }
            .subtitle { color: #555555; font-size: 1.1rem; font-weight: bold; margin-top: 0px; margin-bottom: 2px; }
            hr { margin-top: 2px !important; margin-bottom: 15px !important; border: 0; border-top: 1px solid #EEEEEE; }
            
            /* 4. 按钮统一样式：包括查询按钮和新增的下载按钮 */
            button[kind="primary"], .stDownloadButton button {
                background-color: #1E88E5 !important;
                color: white !important;
                border-radius: 4px !important;
                padding: 0.5rem 2.5rem !important;
                font-weight: bold !important;
                border: none !important;
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }
            
            /* 5. 坐标轴 Logo 图标样式复刻 */
            .logo-icon {
                border-left: 3px solid #1E88E5;
                border-bottom: 3px solid #1E88E5;
                width: 32px; height: 32px;
                display: flex; align-items: center; justify-content: center;
            }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        """渲染品牌 Logo 和标题"""
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("""
                <div style="display: flex; align-items: flex-end; margin-bottom: 2px;">
                    <div class="logo-icon">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1E88E5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
                        </svg>
                    </div>
                    <span class="logo-text">StockWise</span>
                </div>
                <p class="subtitle">EasternMarket 商品销量查询系统</p>
                <hr>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🚪 退出登录", key="logout"):
                st.session_state.authenticated = False
                st.rerun()

    @staticmethod
    def render_custom_footer():
        """[新增] 在页面底部显示专业版权信息，防止 main.py 调用报错 """
        st.markdown("""
            <div style='margin-top: 50px; text-align: center; color: #BBBBBB; font-size: 0.8rem; border-top: 1px solid #f9f9f9; padding-top: 20px;'>
                Copyright © 2026 EasternMarket. All rights reserved.
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_footer():
        """显示微型版本号标识"""
        st.markdown("<div style='text-align: right; color: #EEE; font-size: 10px;'>v1.4.2-STABLE</div>", unsafe_allow_html=True)