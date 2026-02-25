import google.genai as genai
import streamlit as st
import json
import re
from typing import Dict, List, Optional
import pandas as pd

class AIEngine:
    def __init__(self):
        """初始化 AI 引擎"""
        self.api_key = None
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """初始化 Gemini API"""
        try:
            # 尝试从环境变量获取 API Key
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                st.warning("⚠️ 未设置 GEMINI_API_KEY 环境变量")
                return
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            st.success("✅ Gemini API 初始化成功")
            
        except Exception as e:
            st.error(f"❌ Gemini API 初始化失败: {str(e)}")
    
    def is_available(self) -> bool:
        """检查 AI 服务是否可用"""
        return self.model is not None
    
    def classify_product(self, product_info: Dict) -> Dict:
        """智能商品分类"""
        if not self.is_available():
            return {"error": "AI 服务不可用"}
        
        try:
            # 构建分类提示
            prompt = self._build_classification_prompt(product_info)
            
            # 调用 Gemini API
            response = self.model.generate_content(prompt)
            
            # 解析响应
            classification = self._parse_classification_response(response.text)
            
            return classification
            
        except Exception as e:
            return {"error": f"分类失败: {str(e)}"}
    
    def generate_description(self, product_info: Dict, target_length: str = "medium") -> Dict:
        """生成商品智能描述"""
        if not self.is_available():
            return {"error": "AI 服务不可用"}
        
        try:
            # 构建描述生成提示
            prompt = self._build_description_prompt(product_info, target_length)
            
            # 调用 Gemini API
            response = self.model.generate_content(prompt)
            
            # 解析响应
            description = self._parse_description_response(response.text)
            
            return description
            
        except Exception as e:
            return {"error": f"描述生成失败: {str(e)}"}
    
    def batch_classify_products(self, products: List[Dict]) -> List[Dict]:
        """批量商品分类"""
        results = []
        for i, product in enumerate(products):
            with st.spinner(f"正在分类第 {i+1}/{len(products)} 个商品..."):
                result = self.classify_product(product)
                results.append({
                    "product_id": product.get("id"),
                    "product_name": product.get("name"),
                    **result
                })
        return results
    
    def batch_generate_descriptions(self, products: List[Dict], target_length: str = "medium") -> List[Dict]:
        """批量生成商品描述"""
        results = []
        for i, product in enumerate(products):
            with st.spinner(f"正在生成第 {i+1}/{len(products)} 个商品描述..."):
                result = self.generate_description(product, target_length)
                results.append({
                    "product_id": product.get("id"),
                    "product_name": product.get("name"),
                    **result
                })
        return results
    
    def _build_classification_prompt(self, product_info: Dict) -> str:
        """构建分类提示"""
        name = product_info.get("name", "")
        sku = product_info.get("sku", "")
        code = product_info.get("code", "")
        price = product_info.get("price", 0)
        
        prompt = f"""
请对以下商品进行智能分类，返回JSON格式的结果：

商品信息：
- 名称：{name}
- SKU：{sku}
- 商品编码：{code}
- 价格：${price:.2f}

请按照以下维度进行分类：

1. 主类别（如：生鲜、日用品、零食、饮料、调料、粮油等）
2. 子类别（如：蔬菜、水果、肉类、乳制品、清洁用品、个人护理等）
3. 商品属性（如：有机、进口、本地、冷冻、常温等）
4. 目标客户（如：家庭、个人、餐饮、批发等）
5. 存储要求（如：冷藏、冷冻、常温、干燥等）

请返回严格的JSON格式：
{{
    "main_category": "主类别",
    "sub_category": "子类别", 
    "attributes": ["属性1", "属性2"],
    "target_customers": ["目标客户1", "目标客户2"],
    "storage_requirements": "存储要求",
    "confidence_score": 0.95
}}
"""
        return prompt
    
    def _build_description_prompt(self, product_info: Dict, target_length: str) -> str:
        """构建描述生成提示"""
        name = product_info.get("name", "")
        sku = product_info.get("sku", "")
        code = product_info.get("code", "")
        price = product_info.get("price", 0)
        
        length_map = {
            "short": "50-80字",
            "medium": "100-150字", 
            "long": "200-250字"
        }
        target_chars = length_map.get(target_length, "100-150字")
        
        prompt = f"""
请为以下商品生成吸引人的营销描述：

商品信息：
- 名称：{name}
- SKU：{sku}
- 商品编码：{code}
- 价格：${price:.2f}

要求：
1. 描述长度：{target_chars}
2. 突出商品特色和优势
3. 语言生动有吸引力
4. 适合超市营销场景
5. 包含使用场景或食用建议

请返回JSON格式：
{{
    "description": "生成的商品描述",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "selling_points": ["卖点1", "卖点2"],
    "usage_suggestions": "使用建议",
    "confidence_score": 0.90
}}
"""
        return prompt
    
    def _parse_classification_response(self, response_text: str) -> Dict:
        """解析分类响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "无法解析AI响应", "raw_response": response_text}
        except json.JSONDecodeError:
            return {"error": "JSON解析失败", "raw_response": response_text}
    
    def _parse_description_response(self, response_text: str) -> Dict:
        """解析描述响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果没有JSON格式，直接返回文本作为描述
                return {
                    "description": response_text.strip(),
                    "keywords": [],
                    "selling_points": [],
                    "usage_suggestions": "",
                    "confidence_score": 0.8
                }
        except json.JSONDecodeError:
            return {
                "description": response_text.strip(),
                "keywords": [],
                "selling_points": [],
                "usage_suggestions": "",
                "confidence_score": 0.8
            }
    
    def get_category_suggestions(self, inventory: List[Dict]) -> List[str]:
        """获取分类建议"""
        if not inventory:
            return []
        
        # 分析商品名称，提取常见分类
        categories = set()
        for product in inventory[:50]:  # 分析前50个商品
            name = product.get("name", "").lower()
            if any(word in name for word in ["蔬菜", "青菜", "白菜", "萝卜", "土豆"]):
                categories.add("蔬菜")
            if any(word in name for word in ["水果", "苹果", "香蕉", "橙子"]):
                categories.add("水果")
            if any(word in name for word in ["肉", "鸡", "猪", "牛", "鱼"]):
                categories.add("肉类")
            if any(word in name for word in ["奶", "酸奶", "奶酪"]):
                categories.add("乳制品")
            if any(word in name for word in ["饮料", "水", "果汁", "茶"]):
                categories.add("饮料")
            if any(word in name for word in ["零食", "薯片", "饼干", "糖果"]):
                categories.add("零食")
        
        return sorted(list(categories))
