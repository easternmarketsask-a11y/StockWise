import streamlit as st
import pandas as pd
from typing import List, Dict
import json
from ai_engine import AIEngine

class ProductAIManager:
    def __init__(self, api_handler):
        self.api = api_handler
        self.ai_engine = AIEngine()
        self.classification_cache = {}
        self.description_cache = {}
    
    def render_ai_dashboard(self, inventory: List[Dict]):
        """渲染 AI 管理仪表板"""
        st.markdown("### 🤖 商品智能管理")
        
        if not inventory:
            st.warning("请先加载商品数据")
            return
        
        # 检查 AI 服务状态
        if not self.ai_engine.is_available():
            st.error("❌ AI 服务不可用，请检查 GEMINI_API_KEY 环境变量")
            st.info("📝 设置方法：在 Cloud Run 部署时添加环境变量 GEMINI_API_KEY=your_api_key")
            return
        
        # 功能选择
        feature_tabs = st.tabs(["🏷️ 智能分类", "📝 智能描述", "🔄 批量处理", "📊 分类统计"])
        
        with feature_tabs[0]:
            self._render_classification_tab(inventory)
        
        with feature_tabs[1]:
            self._render_description_tab(inventory)
        
        with feature_tabs[2]:
            self._render_batch_processing_tab(inventory)
        
        with feature_tabs[3]:
            self._render_classification_stats_tab(inventory)
    
    def _render_classification_tab(self, inventory: List[Dict]):
        """渲染智能分类标签页"""
        st.markdown("#### 🏷️ 商品智能分类")
        
        # 商品选择
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_product = st.selectbox(
                "选择商品",
                options=inventory,
                format_func=lambda x: f"{x.get('name', 'Unknown')} (${x.get('price', 0):.2f})",
                key="classification_product_select"
            )
        
        with col2:
            if st.button("🔍 开始分类", type="primary", key="classify_single"):
                if selected_product:
                    with st.spinner("AI 正在分析商品..."):
                        result = self.ai_engine.classify_product(selected_product)
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            self._display_classification_result(selected_product, result)
                            # 缓存结果
                            self.classification_cache[selected_product.get("id")] = result
    
    def _render_description_tab(self, inventory: List[Dict]):
        """渲染智能描述标签页"""
        st.markdown("#### 📝 商品智能描述生成")
        
        # 商品选择
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_product = st.selectbox(
                "选择商品",
                options=inventory,
                format_func=lambda x: f"{x.get('name', 'Unknown')} (${x.get('price', 0):.2f})",
                key="description_product_select"
            )
        
        with col2:
            description_length = st.selectbox(
                "描述长度",
                options=["short", "medium", "long"],
                format_func=lambda x: {"short": "简短 (50-80字)", "medium": "中等 (100-150字)", "long": "详细 (200-250字)"}[x],
                key="description_length"
            )
        
        with col3:
            if st.button("✨ 生成描述", type="primary", key="generate_description"):
                if selected_product:
                    with st.spinner("AI 正在生成描述..."):
                        result = self.ai_engine.generate_description(selected_product, description_length)
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            self._display_description_result(selected_product, result)
                            # 缓存结果
                            cache_key = f"{selected_product.get('id')}_{description_length}"
                            self.description_cache[cache_key] = result
    
    def _render_batch_processing_tab(self, inventory: List[Dict]):
        """渲染批量处理标签页"""
        st.markdown("#### 🔄 批量智能处理")
        
        # 批量处理选项
        col1, col2 = st.columns(2)
        with col1:
            batch_size = st.slider("批量处理数量", min_value=1, max_value=50, value=10, key="batch_size")
            process_type = st.selectbox("处理类型", ["分类", "描述生成", "分类+描述"], key="batch_process_type")
        
        with col2:
            description_length = st.selectbox(
                "描述长度",
                options=["short", "medium", "long"],
                format_func=lambda x: {"short": "简短", "medium": "中等", "long": "详细"}[x],
                key="batch_description_length"
            )
        
        # 商品选择
        st.markdown("**选择要处理的商品：**")
        selected_products = st.multiselect(
            "商品列表",
            options=inventory,
            format_func=lambda x: f"{x.get('name', 'Unknown')} (${x.get('price', 0):.2f})",
            default=inventory[:batch_size],
            key="batch_product_select"
        )
        
        if st.button("🚀 开始批量处理", type="primary", key="start_batch_process"):
            if selected_products:
                self._process_batch(selected_products, process_type, description_length)
            else:
                st.warning("请选择要处理的商品")
    
    def _render_classification_stats_tab(self, inventory: List[Dict]):
        """渲染分类统计标签页"""
        st.markdown("#### 📊 分类统计分析")
        
        # 获取已分类的商品
        classified_products = []
        for product in inventory:
            product_id = product.get("id")
            if product_id in self.classification_cache:
                classified_data = self.classification_cache[product_id]
                if "main_category" in classified_data:
                    classified_products.append({
                        "product_id": product_id,
                        "product_name": product.get("name"),
                        "price": product.get("price", 0),
                        **classified_data
                    })
        
        if not classified_products:
            st.info("暂无已分类的商品，请先进行分类操作")
            return
        
        # 转换为 DataFrame 进行分析
        df = pd.DataFrame(classified_products)
        
        # 主类别统计
        st.markdown("##### 📈 主类别分布")
        main_category_counts = df["main_category"].value_counts()
        st.bar_chart(main_category_counts)
        
        # 子类别统计
        st.markdown("##### 📊 子类别分布")
        sub_category_counts = df["sub_category"].value_counts()
        st.bar_chart(sub_category_counts)
        
        # 详细数据表
        st.markdown("##### 📋 分类详情")
        display_df = df[["product_name", "price", "main_category", "sub_category", "confidence_score"]].copy()
        display_df["price"] = display_df["price"].map(lambda x: f"${x:.2f}")
        display_df["confidence_score"] = display_df["confidence_score"].map(lambda x: f"{x:.2%}")
        st.dataframe(display_df, use_container_width=True)
        
        # 导出分类结果
        if st.button("📥 导出分类结果"):
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "💾 下载分类结果.csv",
                csv,
                "product_classifications.csv",
                "text/csv"
            )
    
    def _display_classification_result(self, product: Dict, result: Dict):
        """显示分类结果"""
        st.markdown("##### 🏷️ 分类结果")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**商品名称：** {product.get('name')}")
            st.markdown(f"**商品价格：** ${product.get('price', 0):.2f}")
        
        with col2:
            confidence = result.get("confidence_score", 0)
            st.markdown(f"**置信度：** {confidence:.2%}")
            if confidence >= 0.8:
                st.success("高置信度")
            elif confidence >= 0.6:
                st.warning("中等置信度")
            else:
                st.error("低置信度")
        
        # 分类详情
        st.markdown("###### 📋 分类详情")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**主类别：** {result.get('main_category', 'N/A')}")
            st.markdown(f"**子类别：** {result.get('sub_category', 'N/A')}")
            st.markdown(f"**存储要求：** {result.get('storage_requirements', 'N/A')}")
        
        with col2:
            attributes = result.get('attributes', [])
            if attributes:
                st.markdown("**商品属性：**")
                for attr in attributes:
                    st.markdown(f"• {attr}")
            
            customers = result.get('target_customers', [])
            if customers:
                st.markdown("**目标客户：**")
                for customer in customers:
                    st.markdown(f"• {customer}")
    
    def _display_description_result(self, product: Dict, result: Dict):
        """显示描述结果"""
        st.markdown("##### ✨ 生成的描述")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**商品名称：** {product.get('name')}")
            st.markdown(f"**商品价格：** ${product.get('price', 0):.2f}")
        
        with col2:
            confidence = result.get("confidence_score", 0)
            st.markdown(f"**置信度：** {confidence:.2%}")
        
        # 描述内容
        st.markdown("###### 📝 商品描述")
        description = result.get('description', '')
        if description:
            st.info(description)
        
        # 关键词和卖点
        col1, col2 = st.columns(2)
        with col1:
            keywords = result.get('keywords', [])
            if keywords:
                st.markdown("**关键词：**")
                for keyword in keywords:
                    st.markdown(f"• {keyword}")
        
        with col2:
            selling_points = result.get('selling_points', [])
            if selling_points:
                st.markdown("**主要卖点：**")
                for point in selling_points:
                    st.markdown(f"• {point}")
        
        # 使用建议
        usage_suggestions = result.get('usage_suggestions', '')
        if usage_suggestions:
            st.markdown("###### 💡 使用建议")
            st.success(usage_suggestions)
    
    def _process_batch(self, products: List[Dict], process_type: str, description_length: str):
        """处理批量任务"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, product in enumerate(products):
            status_text.text(f"正在处理第 {i+1}/{len(products)} 个商品...")
            progress_bar.progress((i + 1) / len(products))
            
            product_result = {"product_id": product.get("id"), "product_name": product.get("name")}
            
            # 分类处理
            if process_type in ["分类", "分类+描述"]:
                classification_result = self.ai_engine.classify_product(product)
                product_result["classification"] = classification_result
            
            # 描述生成处理
            if process_type in ["描述生成", "分类+描述"]:
                description_result = self.ai_engine.generate_description(product, description_length)
                product_result["description"] = description_result
            
            results.append(product_result)
        
        progress_bar.empty()
        status_text.text("✅ 批量处理完成！")
        
        # 显示结果摘要
        st.markdown("##### 📊 处理结果摘要")
        
        success_count = 0
        error_count = 0
        
        for result in results:
            if process_type in ["分类", "分类+描述"]:
                if "classification" in result and "error" not in result["classification"]:
                    success_count += 1
                else:
                    error_count += 1
            elif process_type == "描述生成":
                if "description" in result and "error" not in result["description"]:
                    success_count += 1
                else:
                    error_count += 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("处理总数", len(results))
        with col2:
            st.metric("成功", success_count, delta_color="normal")
        with col3:
            st.metric("失败", error_count, delta_color="inverse")
        
        # 详细结果
        st.markdown("##### 📋 详细结果")
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)
        
        # 导出结果
        if st.button("📥 导出批量处理结果"):
            json_results = json.dumps(results, ensure_ascii=False, indent=2)
            st.download_button(
                "💾 下载处理结果.json",
                json_results,
                "batch_processing_results.json",
                "application/json"
            )
