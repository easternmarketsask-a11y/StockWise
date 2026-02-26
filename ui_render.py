import streamlit as st

class UIRenderer:
    @staticmethod
    def apply_style():
        st.markdown("""
            <style>
            /* 1. 让LOGO真正置顶 - 移除顶部间距 */
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                max-width: 800px !important; /* 保持专业居中感 */
            }
            
            /* 2. 背景与标题文字颜色 */
            .stApp { background-color: #FFFFFF !important; }
            .logo-text { color: #1E88E5; font-family: sans-serif; font-weight: bold; font-size: 2.3rem; margin-left: 10px; line-height: 1; }
            
            /* 3. 副标题与横线间距极致压缩 */
            .subtitle { color: #555555; font-size: 1.1rem; font-weight: bold; margin-top: 0px; margin-bottom: 2px; }
            hr { margin-top: 2px !important; margin-bottom: 15px !important; border: 0; border-top: 1px solid #EEEEEE; }
            
            /* 4. 按钮样式 */
            button[kind="primary"] {
                background-color: #1E88E5 !important;
                color: white !important;
                border-radius: 4px !important;
                padding: 0.5rem 2.5rem !important;
                font-weight: bold !important;
            }
            
            /* 5. 坐标轴 Logo 尺寸优化 */
            .logo-icon {
                border-left: 3px solid #1E88E5;
                border-bottom: 3px solid #1E88E5;
                width: 32px; height: 32px;
                display: flex; align-items: center; justify-content: center;
            }

            /* 追加：隐藏 Streamlit 默认页脚水印 */
            footer {visibility: hidden;}
            header {visibility: visible;}
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        # 完全复刻您的 Logo 图片，并消除所有默认 Margin
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

    @staticmethod
    def render_footer():
        st.markdown("<div style='text-align: right; color: #EEE; font-size: 17px; margin-top: 30px;'>v1.3.3-STABLE</div>", unsafe_allow_html=True)

         # 增加一个专门渲染页脚版权的方法
    @staticmethod
    def render_custom_footer():
        st.markdown("""
            <div style='margin-top: 100px; text-align: center; color: #BBBBBB; font-size: 0.8rem; border-top: 1px solid #f0f2f6; padding-top: 20px;'>
                Copyright © 2026 EasternMarket. All rights reserved.
            </div>
        """, unsafe_allow_html=True)