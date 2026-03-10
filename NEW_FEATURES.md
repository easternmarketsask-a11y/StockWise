# StockWise 新功能文档

## 版本 2.2.0 - 商品管理与AI增强功能

### 🎯 功能概述

本次更新在**保持所有现有功能完整运行**的前提下，新增了以下核心功能：

1. **后端商品信息管理** - 商品数据可在后端编辑和持久化存储
2. **AI结果后端存储** - AI处理结果保存在后端，可编辑和管理
3. **食谱推荐生成** - AI生成商品相关的食谱推荐
4. **商品图片提示词生成** - AI生成用于图片生成工具的提示词
5. **完整数据导出** - 支持导出商品和AI结果数据供外部网站使用

---

## 📦 新增模块

### 1. `product_manager.py` - 商品管理模块
**功能：** 提供商品信息的后端存储和编辑能力

**核心方法：**
- `save_product(product_data)` - 保存或更新商品信息
- `update_product_field(product_key, field, value)` - 更新单个字段
- `get_all_products(filters)` - 获取商品列表（支持筛选）
- `bulk_update(updates)` - 批量更新商品
- `export_products(format)` - 导出商品数据（JSON/CSV）
- `get_statistics()` - 获取商品统计信息

**存储位置：** `data/products.json`

### 2. `ai_results_store.py` - AI结果存储模块
**功能：** 持久化存储所有AI处理结果

**核心方法：**
- `save_classification(product_info, classification)` - 保存分类结果
- `save_description(product_info, description)` - 保存描述结果
- `save_recipe(product_info, recipe)` - 保存食谱结果
- `save_image_info(product_info, image_info)` - 保存图片提示词
- `update_result_field(product_key, result_type, field, value)` - 编辑结果字段
- `get_all_results(filters)` - 获取AI结果列表
- `export_results(format, result_types)` - 导出AI结果
- `merge_with_products(products)` - 合并商品和AI结果

**存储位置：** `data/ai_results.json`

### 3. `ai_enhancements.py` - AI增强功能模块
**功能：** 提供食谱推荐和图片提示词生成

**核心方法：**
- `generate_recipe(product_info, recipe_type)` - 生成单个食谱
  - recipe_type: `simple` (简单易做), `detailed` (详细步骤), `creative` (创意料理)
- `generate_image_prompt(product_info, style)` - 生成图片提示词
  - style: `realistic` (真实摄影), `artistic` (艺术插画), `minimalist` (极简主义), `lifestyle` (生活场景)
- `batch_generate_recipes(products, recipe_type)` - 批量生成食谱
- `batch_generate_image_prompts(products, style)` - 批量生成图片提示词

**AI提供商：** 支持 Anthropic Claude 和 Google Gemini

---

## 🔌 新增API端点

### 商品管理 API

#### GET `/api/products/managed`
获取所有管理的商品
- **查询参数：**
  - `search` - 搜索关键词
  - `category` - 按类别筛选
  - `has_description` - 是否有描述
- **返回：** 商品列表和统计信息

#### POST `/api/products/save`
保存或更新商品信息
- **请求体：** 商品数据对象
- **返回：** 保存后的商品数据

#### PUT `/api/products/{product_key}/field`
更新商品的单个字段
- **请求体：** `{ "field": "字段名", "value": "新值" }`
- **返回：** 更新后的商品数据

#### POST `/api/products/bulk-update`
批量更新多个商品
- **请求体：** `{ "updates": [{ "product_key": "...", "fields": {...} }] }`
- **返回：** 批量更新结果

#### GET `/api/products/export`
导出商品数据
- **查询参数：** `format` - `json` 或 `csv`
- **返回：** 导出的商品数据

#### GET `/api/products/merged`
获取商品和AI结果的合并数据
- **返回：** 包含所有AI结果的完整商品数据

### AI结果管理 API

#### GET `/api/ai-results`
获取所有AI处理结果
- **查询参数：**
  - `search` - 搜索关键词
  - `category` - 按类别筛选
  - `has_classification` - 是否有分类
  - `has_description` - 是否有描述
  - `has_recipe` - 是否有食谱
  - `has_image` - 是否有图片提示
- **返回：** AI结果列表和统计信息

#### POST `/api/ai-results/save-classification`
保存AI分类结果到后端
- **请求体：** `{ "product_info": {...}, "classification": {...} }`
- **返回：** 保存的结果

#### POST `/api/ai-results/save-description`
保存AI描述结果到后端
- **请求体：** `{ "product_info": {...}, "description": {...} }`
- **返回：** 保存的结果

#### PUT `/api/ai-results/{product_key}/edit`
编辑AI结果的特定字段
- **请求体：** `{ "result_type": "classification|description|recipe|image_info", "field": "字段名", "value": "新值" }`
- **返回：** 更新后的结果

#### GET `/api/ai-results/export`
导出AI结果
- **查询参数：**
  - `format` - `json` 或 `csv`
  - `result_types` - 要导出的结果类型（逗号分隔）
- **返回：** 导出的AI结果数据

### AI增强功能 API

#### POST `/api/ai/recipe`
生成单个商品的食谱推荐
- **请求体：** `{ "product_info": { "name": "商品名" }, "recipe_type": "simple|detailed|creative" }`
- **返回：** 生成的食谱（自动保存到后端）

#### POST `/api/ai/image-prompt`
生成单个商品的图片提示词
- **请求体：** `{ "product_info": { "name": "商品名" }, "style": "realistic|artistic|minimalist|lifestyle" }`
- **返回：** 生成的图片提示词（自动保存到后端）

#### POST `/api/ai/batch-recipe`
批量生成食谱推荐
- **请求体：** `{ "products": [...], "recipe_type": "simple|detailed|creative" }`
- **返回：** 批量生成结果

#### POST `/api/ai/batch-image-prompt`
批量生成图片提示词
- **请求体：** `{ "products": [...], "style": "realistic|artistic|minimalist|lifestyle" }`
- **返回：** 批量生成结果

---

## 🎨 新增UI组件

### 商品管理标签页（🛠️ 商品管理）

#### 子标签1：📝 商品编辑
- **加载商品列表** - 从后端加载所有管理的商品
- **导出商品数据** - 导出商品信息为JSON格式
- **导出完整数据** - 导出包含AI结果的完整数据
- **商品统计** - 显示总商品数、有描述、有分类、完成度

#### 子标签2：🤖 AI结果管理
- **加载AI结果** - 从后端加载所有AI处理结果
- **导出AI结果** - 导出AI结果为JSON格式
- **结果统计** - 显示总结果数、有分类、有描述、有食谱

#### 子标签3：🍳 食谱生成
- **单个生成** - 输入商品名称生成食谱
- **批量生成** - 为勾选的商品批量生成食谱
- **食谱类型选择** - 简单易做、详细步骤、创意料理
- **食谱展示** - 显示完整的食谱信息（食材、步骤、技巧）

#### 子标签4：🖼️ 图片提示词
- **单个生成** - 输入商品名称生成图片提示词
- **批量生成** - 为勾选的商品批量生成提示词
- **风格选择** - 真实摄影、艺术插画、极简主义、生活场景
- **提示词展示** - 显示英文提示词、中文描述、参数建议

---

## 🔒 安全保护措施

### 现有功能完全保护
根据记忆中的核心逻辑锁定要求，所有新功能均：

1. ✅ **作为新端点添加** - 不修改任何现有API端点
2. ✅ **使用独立模块** - 所有新功能在独立文件中实现
3. ✅ **不改变现有JavaScript** - 新增事件处理器，不修改现有函数
4. ✅ **不修改HTML元素ID** - 现有UI元素保持不变
5. ✅ **保持向后兼容** - 所有现有功能继续正常工作
6. ✅ **使用原始字符串** - 遵循JavaScript模板字符串规则

### 已验证的现有功能
以下功能确认不受影响：
- ✅ 销量查询 (`/api/sales/search`)
- ✅ CSV导出 (`/api/sales/export`)
- ✅ 库存预警 (`/api/inventory/alerts`)
- ✅ 趋势分析 (`/api/trends/analysis`)
- ✅ AI分类 (`/api/ai/classify`)
- ✅ AI描述 (`/api/ai/describe`)
- ✅ 分类管理 (`/api/categories/*`)
- ✅ 图表数据 (`/api/charts/*`)
- ✅ 所有按钮和链接
- ✅ 标签页切换
- ✅ 搜索和筛选功能

---

## 📊 数据存储

### 存储位置
- **商品数据：** `data/products.json`
- **AI结果：** `data/ai_results.json`

### 数据格式

#### 商品数据示例
```json
{
  "id_ABC123": {
    "id": "ABC123",
    "name": "商品名称",
    "sku": "SKU001",
    "code": "CODE001",
    "price": 9.99,
    "description": "商品描述",
    "category": "类别",
    "created_at": "2026-03-10T14:00:00",
    "updated_at": "2026-03-10T14:00:00"
  }
}
```

#### AI结果数据示例
```json
{
  "id_ABC123": {
    "product_info": {
      "id": "ABC123",
      "name": "商品名称",
      "sku": "SKU001"
    },
    "classification": {
      "main_category": "主类别",
      "sub_category": "子类别",
      "confidence_score": 0.95
    },
    "description": {
      "description": "营销描述",
      "keywords": ["关键词1", "关键词2"]
    },
    "recipe": {
      "recipe_name": "食谱名称",
      "ingredients": [...],
      "steps": [...]
    },
    "image_info": {
      "prompt_en": "English prompt",
      "style": "realistic"
    },
    "created_at": "2026-03-10T14:00:00",
    "updated_at": "2026-03-10T14:00:00"
  }
}
```

---

## 🚀 使用指南

### 1. 商品信息管理
1. 进入 **🛠️ 商品管理** 标签页
2. 点击 **📝 商品编辑** 子标签
3. 点击 **加载商品列表** 查看所有商品
4. 使用 **导出商品数据** 或 **导出完整数据** 导出数据

### 2. AI结果管理
1. 在 **🛠️ 商品管理** 标签页
2. 点击 **🤖 AI结果管理** 子标签
3. 点击 **加载AI结果** 查看所有AI处理结果
4. 使用 **导出AI结果** 导出数据

### 3. 生成食谱推荐
**单个商品：**
1. 在 **🛠️ 商品管理** 标签页
2. 点击 **🍳 食谱生成** 子标签
3. 输入商品名称，选择食谱类型
4. 点击 **生成食谱** 按钮

**批量生成：**
1. 在 **📦 销量查询** 标签页勾选商品
2. 切换到 **🛠️ 商品管理** → **🍳 食谱生成**
3. 选择食谱类型
4. 点击 **批量生成食谱** 按钮

### 4. 生成图片提示词
**单个商品：**
1. 在 **🛠️ 商品管理** 标签页
2. 点击 **🖼️ 图片提示词** 子标签
3. 输入商品名称，选择图片风格
4. 点击 **生成提示词** 按钮

**批量生成：**
1. 在 **📦 销量查询** 标签页勾选商品
2. 切换到 **🛠️ 商品管理** → **🖼️ 图片提示词**
3. 选择图片风格
4. 点击 **批量生成提示词** 按钮

### 5. 导出数据供外部网站使用
**方式1：通过UI导出**
- 在商品管理或AI结果管理页面点击导出按钮
- 选择JSON或CSV格式
- 下载文件后可用于其他网站

**方式2：通过API直接调用**
```bash
# 导出商品数据（JSON）
curl https://your-domain.com/api/products/export?format=json

# 导出商品数据（CSV）
curl https://your-domain.com/api/products/export?format=csv

# 导出完整数据（含AI结果）
curl https://your-domain.com/api/products/merged

# 导出AI结果
curl https://your-domain.com/api/ai-results/export?format=json
```

---

## 🔧 环境要求

### 必需的环境变量
- `CLOVER_API_KEY` - Clover POS API密钥（必需）
- `MERCHANT_ID` - 商户ID（必需）
- `ANTHROPIC_API_KEY` - Anthropic AI密钥（可选，用于AI功能）
- `GEMINI_API_KEY` - Google Gemini AI密钥（可选，用于AI功能）

### 依赖项
所有依赖已包含在 `requirements.txt` 中，无需额外安装。

---

## 📝 注意事项

1. **数据持久化：** 所有商品和AI结果数据保存在 `data/` 目录，确保该目录有写入权限
2. **AI功能：** 需要配置 ANTHROPIC_API_KEY 或 GEMINI_API_KEY 才能使用AI增强功能
3. **现有功能：** 所有现有功能完全不受影响，继续正常工作
4. **数据导出：** 导出的数据可直接用于其他网站或应用程序
5. **批量操作：** 批量生成功能会自动将结果保存到后端存储

---

## 🎉 总结

本次更新成功实现了：
- ✅ 商品信息后端可编辑和保存
- ✅ AI处理结果后端持久化存储和编辑
- ✅ AI食谱推荐功能（单个和批量）
- ✅ AI图片提示词生成功能（单个和批量）
- ✅ 完整数据导出功能供外部网站使用
- ✅ 所有现有功能保持完整运行
- ✅ 遵循严格的代码保护规则

**版本：** 2.2.0  
**更新日期：** 2026年3月10日  
**兼容性：** 完全向后兼容，不影响任何现有功能
