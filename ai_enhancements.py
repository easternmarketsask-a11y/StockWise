"""
AI Enhancements Module - Recipe recommendations and image generation
Provides advanced AI features for product enhancement
"""
import json
import logging
import os
from typing import Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class AIEnhancementsEngine:
    """Handles advanced AI features: recipes and image generation"""
    
    def __init__(self):
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        
        # Initialize AI clients if keys available
        self.anthropic_client = None
        self.gemini_client = None
        
        if self.anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
        
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic API not configured")
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        if not self.gemini_client:
            raise RuntimeError("Gemini API not configured")
        
        try:
            response = self.gemini_client.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from AI response"""
        text = text.strip()
        
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()
        
        # Remove any leading/trailing non-JSON characters
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            text = text[start_idx:end_idx]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, text: {text[:200]}")
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
    
    def generate_recipe(self, product_info: Dict, recipe_type: str = "simple") -> Dict:
        """Generate recipe recommendations for a product
        
        Args:
            product_info: Product information dict with name, category, etc.
            recipe_type: Type of recipe (simple, detailed, creative)
        
        Returns:
            Dict with recipe information
        """
        name = product_info.get("name", "")
        category = product_info.get("category", "")
        
        if recipe_type == "simple":
            complexity = "简单易做，适合家庭日常"
        elif recipe_type == "detailed":
            complexity = "详细步骤，适合烹饪爱好者"
        else:
            complexity = "创意料理，适合尝试新口味"
        
        prompt = f'''请为以下商品生成食谱推荐，返回严格的JSON格式：

{{
  "recipe_name": "食谱名称",
  "recipe_name_en": "Recipe Name in English",
  "cuisine_type": "菜系类型",
  "difficulty": "简单/中等/困难",
  "prep_time": "准备时间（分钟）",
  "cook_time": "烹饪时间（分钟）",
  "servings": "份数",
  "ingredients": [
    {{"item": "主要食材", "amount": "用量", "notes": "备注"}},
    {{"item": "配料", "amount": "用量", "notes": "备注"}}
  ],
  "steps": [
    {{"step": 1, "instruction": "步骤说明", "tip": "小贴士"}},
    {{"step": 2, "instruction": "步骤说明", "tip": "小贴士"}}
  ],
  "tips": ["烹饪技巧1", "烹饪技巧2"],
  "nutrition_highlights": ["营养亮点1", "营养亮点2"],
  "pairing_suggestions": ["搭配建议1", "搭配建议2"],
  "storage_tips": "储存建议",
  "confidence_score": 0.90
}}

商品信息：
- 商品名称: {name}
- 商品类别: {category}
- SKU: {product_info.get("sku", "")}
- 价格: ${product_info.get("price", 0)}

食谱要求: {complexity}

请确保食谱实用、准确，适合该商品特点。如果商品不适合做食谱（如非食品），请在recipe_name中说明"不适用"并给出原因。
'''
        
        # Try Anthropic first, fallback to Gemini
        try:
            if self.anthropic_client:
                response_text = self._call_anthropic(prompt)
            elif self.gemini_client:
                response_text = self._call_gemini(prompt)
            else:
                raise RuntimeError("No AI provider configured")
            
            result = self._extract_json(response_text)
            result["ai_provider"] = "anthropic" if self.anthropic_client else "gemini"
            result["generated_at"] = __import__('datetime').datetime.now().isoformat()
            
            return result
        
        except Exception as e:
            logger.error(f"Recipe generation failed: {e}")
            raise
    
    def generate_image_prompt(self, product_info: Dict, style: str = "realistic") -> Dict:
        """Generate image prompt for product visualization
        
        Args:
            product_info: Product information
            style: Image style (realistic, artistic, minimalist, lifestyle)
        
        Returns:
            Dict with image generation prompt and metadata
        """
        name = product_info.get("name", "")
        category = product_info.get("category", "")
        description = product_info.get("description", "")
        
        style_guides = {
            "realistic": "真实摄影风格，高清细节，专业商品摄影",
            "artistic": "艺术插画风格，色彩丰富，创意表现",
            "minimalist": "极简主义风格，干净背景，突出商品",
            "lifestyle": "生活场景风格，自然光线，使用场景展示"
        }
        
        style_guide = style_guides.get(style, style_guides["realistic"])
        
        prompt = f'''请为以下商品生成图片描述提示词（用于AI图片生成），返回严格的JSON格式：

{{
  "prompt_en": "Detailed English prompt for image generation",
  "prompt_zh": "详细的中文图片描述",
  "negative_prompt": "Negative prompt to avoid unwanted elements",
  "style": "图片风格",
  "composition": "构图建议",
  "lighting": "光线建议",
  "color_palette": ["主色调1", "主色调2"],
  "key_elements": ["关键元素1", "关键元素2"],
  "recommended_size": "推荐尺寸（如 1024x1024）",
  "recommended_model": "推荐的AI模型",
  "confidence_score": 0.90
}}

商品信息：
- 商品名称: {name}
- 商品类别: {category}
- 商品描述: {description}
- SKU: {product_info.get("sku", "")}

风格要求: {style_guide}

请生成专业、准确的图片提示词，适合用于Stable Diffusion、DALL-E或Midjourney等AI图片生成工具。
'''
        
        try:
            if self.anthropic_client:
                response_text = self._call_anthropic(prompt)
            elif self.gemini_client:
                response_text = self._call_gemini(prompt)
            else:
                raise RuntimeError("No AI provider configured")
            
            result = self._extract_json(response_text)
            result["ai_provider"] = "anthropic" if self.anthropic_client else "gemini"
            result["generated_at"] = __import__('datetime').datetime.now().isoformat()
            result["style_requested"] = style
            
            return result
        
        except Exception as e:
            logger.error(f"Image prompt generation failed: {e}")
            raise
    
    def batch_generate_recipes(self, products: list, recipe_type: str = "simple") -> Dict:
        """Batch generate recipes for multiple products"""
        results = []
        success_count = 0
        failed_count = 0
        
        for product in products:
            try:
                recipe = self.generate_recipe(product, recipe_type)
                results.append({
                    "product": product,
                    "recipe": recipe,
                    "success": True
                })
                success_count += 1
            except Exception as e:
                results.append({
                    "product": product,
                    "error": str(e),
                    "success": False
                })
                failed_count += 1
        
        return {
            "results": results,
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(products)
        }
    
    def batch_generate_image_prompts(self, products: list, style: str = "realistic") -> Dict:
        """Batch generate image prompts for multiple products"""
        results = []
        success_count = 0
        failed_count = 0
        
        for product in products:
            try:
                image_prompt = self.generate_image_prompt(product, style)
                results.append({
                    "product": product,
                    "image_prompt": image_prompt,
                    "success": True
                })
                success_count += 1
            except Exception as e:
                results.append({
                    "product": product,
                    "error": str(e),
                    "success": False
                })
                failed_count += 1
        
        return {
            "results": results,
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(products)
        }


# Global instance
_ai_enhancements_engine = None

def get_ai_enhancements_engine() -> AIEnhancementsEngine:
    """Get or create global AIEnhancementsEngine instance"""
    global _ai_enhancements_engine
    if _ai_enhancements_engine is None:
        _ai_enhancements_engine = AIEnhancementsEngine()
    return _ai_enhancements_engine
