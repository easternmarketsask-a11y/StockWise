# Firebase 集成设置指南

## 📋 概述

StockWise 现已集成 Firebase，使用 **Firestore** 存储商品结构化数据，使用 **Cloud Storage** 存储商品图片。

## 🏗️ 架构设计

### 存储方案

```
┌─────────────────────────────────────────────────────────────┐
│                      StockWise 应用                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │  Clover POS API  │              │   Firebase       │    │
│  │  (实时数据源)     │◄────同步────►│   (持久化存储)    │    │
│  └──────────────────┘              └──────────────────┘    │
│         │                                    │              │
│         │                                    │              │
│         ▼                                    ▼              │
│  ┌──────────────────┐              ┌──────────────────┐    │
│  │  销售数据         │              │   Firestore      │    │
│  │  库存数据         │              │   商品数据库      │    │
│  └──────────────────┘              └──────────────────┘    │
│                                             │              │
│                                             ▼              │
│                                    ┌──────────────────┐    │
│                                    │ Cloud Storage    │    │
│                                    │ 商品图片存储      │    │
│                                    └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 数据模型

**Firestore 商品文档结构：**

```javascript
{
  id: "auto_generated_id",           // Firestore 自动生成
  clover_id: "CLOVER_ITEM_ID",       // Clover 商品 ID（如果同步）
  name: "商品名称",
  sku: "SKU-12345",
  code: "BARCODE",
  alt_code: "ALT-CODE",
  price: 29.99,
  stock_quantity: 100,
  category: "水果",                   // 分类
  description: "商品详细描述",
  imageUrl: "https://storage.googleapis.com/...",  // Cloud Storage URL
  source: "clover" | "manual",       // 数据来源
  created_at: "2026-03-10T16:00:00",
  updated_at: "2026-03-10T16:00:00",
  last_synced: "2026-03-10T16:00:00"
}
```

## 🚀 快速开始

### 1. 创建 Firebase 项目

1. 访问 [Firebase Console](https://console.firebase.google.com/)
2. 创建新项目或选择现有项目 `stockwise-486801`
3. 启用 **Firestore Database**
4. 启用 **Cloud Storage**

### 2. 配置 Firestore 安全规则

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /products/{productId} {
      // 允许读取所有商品
      allow read: if true;
      
      // 只允许认证用户写入
      allow write: if request.auth != null;
    }
  }
}
```

### 3. 配置 Cloud Storage 安全规则

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /products/{imageId} {
      // 允许读取所有图片
      allow read: if true;
      
      // 只允许认证用户上传（最大 5MB）
      allow write: if request.auth != null 
                   && request.resource.size < 5 * 1024 * 1024;
    }
  }
}
```

### 4. 获取服务账号密钥

#### 方式 A：本地开发

1. Firebase Console → 项目设置 → 服务账号
2. 点击"生成新的私钥"
3. 下载 JSON 文件，保存为 `serviceAccountKey.json`
4. 将文件路径添加到 `.env`：

```bash
FIREBASE_SERVICE_ACCOUNT_PATH=D:/stockwise_final/serviceAccountKey.json
FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com
```

#### 方式 B：Cloud Run 部署

1. 下载服务账号 JSON
2. 将 JSON 内容压缩为单行字符串
3. 在 Cloud Run 中设置环境变量：

```bash
gcloud run services update stockwise-app \
  --set-env-vars="FIREBASE_SERVICE_ACCOUNT_JSON={\"type\":\"service_account\",...}" \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com"
```

### 5. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖：
- `firebase-admin>=6.5.0` - Firebase Admin SDK
- `Pillow>=10.0.0` - 图片压缩处理
- `python-multipart>=0.0.6` - 文件上传支持

## 📚 核心模块说明

### 1. `firebase_config.py` - Firebase 初始化

```python
from firebase_config import get_firestore_client, get_storage_bucket

# 获取 Firestore 客户端
db = get_firestore_client()

# 获取 Storage Bucket
bucket = get_storage_bucket()
```

### 2. `firebase_product_manager.py` - Firestore CRUD

```python
from firebase_product_manager import get_firebase_product_manager

pm = get_firebase_product_manager()

# 创建商品
product = pm.create_product({
    "name": "苹果",
    "price": 5.99,
    "category": "水果",
    "stock_quantity": 100
})

# 获取商品
product = pm.get_product(product_id)

# 更新商品
pm.update_product(product_id, {"price": 6.99})

# 删除商品
pm.delete_product(product_id)

# 按分类查询（带分页）
products = pm.get_products_by_category("水果", limit=50)

# 搜索商品
results = pm.search_products("苹果")

# 获取统计信息
stats = pm.get_statistics()
```

### 3. `firebase_storage_handler.py` - 图片管理

```python
from firebase_storage_handler import get_storage_handler

storage = get_storage_handler()

# 上传图片（自动压缩）
with open("apple.jpg", "rb") as f:
    image_data = f.read()

image_url = storage.upload_image(
    image_data=image_data,
    filename="apple.jpg",
    product_id="product_123",
    compress=True  # 自动压缩到 1200x1200, 85% 质量
)

# 删除图片
storage.delete_image(image_url)

# 列出商品所有图片
urls = storage.list_product_images("product_123")
```

### 4. `firebase_integration.py` - 统一集成

```python
from firebase_integration import get_firebase_integration

integration = get_firebase_integration()

# 从 Clover 同步商品到 Firebase
result = integration.sync_clover_to_firebase(overwrite=False)

# 创建商品并上传图片
product = integration.create_product_with_image(
    product_data={"name": "苹果", "price": 5.99},
    image_data=image_bytes,
    image_filename="apple.jpg"
)

# 更新商品图片
new_url = integration.update_product_image(
    product_id="product_123",
    image_data=new_image_bytes,
    image_filename="new_apple.jpg"
)

# 获取商品（支持筛选和分页）
products = integration.get_products_with_filters(
    category="水果",
    limit=50,
    start_after="last_product_id"
)

# 删除商品和图片
integration.delete_product_with_image("product_123")
```

## 🎯 核心功能

### ✅ 已实现功能

1. **Firestore 数据库操作**
   - ✅ 创建、读取、更新、删除商品
   - ✅ 按分类筛选
   - ✅ 商品搜索（名称、SKU、编码）
   - ✅ 分页加载（Limit/StartAfter）
   - ✅ 统计信息

2. **Cloud Storage 图片管理**
   - ✅ 图片上传（自动生成唯一文件名）
   - ✅ 客户端压缩（最大 1200x1200，85% 质量）
   - ✅ 公开 URL 生成
   - ✅ 图片删除
   - ✅ 批量图片查询

3. **Clover API 集成**
   - ✅ 从 Clover 同步商品到 Firebase
   - ✅ 智能去重（基于 clover_id）
   - ✅ 增量同步支持

## 🔧 API 端点（待集成到 app_server.py）

以下端点将在下一步添加到 `app_server.py`：

```python
# Firebase 商品管理
POST   /api/firebase/products              # 创建商品
GET    /api/firebase/products              # 获取商品列表（支持分页和筛选）
GET    /api/firebase/products/{id}         # 获取单个商品
PUT    /api/firebase/products/{id}         # 更新商品
DELETE /api/firebase/products/{id}         # 删除商品

# 图片上传
POST   /api/firebase/products/{id}/image   # 上传/更新商品图片
DELETE /api/firebase/products/{id}/image   # 删除商品图片

# Clover 同步
POST   /api/firebase/sync-clover           # 从 Clover 同步商品

# 分类管理
GET    /api/firebase/categories            # 获取所有分类
GET    /api/firebase/categories/{name}     # 按分类获取商品

# 统计信息
GET    /api/firebase/statistics            # 获取商品统计
```

## 📊 性能优化

### 1. 图片压缩

- **压缩前**：可能 5-10 MB
- **压缩后**：通常 100-500 KB
- **压缩率**：80-95%
- **质量**：保持高质量（85% JPEG）

### 2. 分页加载

```python
# 第一页
products = pm.get_all_products(limit=50)

# 下一页
last_id = products[-1]['id']
next_page = pm.get_all_products(limit=50, start_after=last_id)
```

### 3. 索引优化

在 Firestore 中为常用查询字段创建索引：
- `category` + `created_at`
- `source` + `updated_at`

## 💰 成本优化建议

### Firestore 成本

- **免费额度**：每天 50,000 次读取，20,000 次写入
- **优化策略**：
  - 使用分页减少单次查询数据量
  - 缓存常用数据
  - 批量操作减少写入次数

### Cloud Storage 成本

- **免费额度**：5 GB 存储，1 GB/天下载
- **优化策略**：
  - 上传前压缩图片（已实现）
  - 删除未使用的图片
  - 使用 CDN 缓存（可选）

## 🔒 安全最佳实践

1. **服务账号密钥保护**
   - ❌ 不要提交到 Git
   - ✅ 使用环境变量
   - ✅ Cloud Run 使用 Secret Manager

2. **Firestore 安全规则**
   - ✅ 限制写入权限
   - ✅ 验证数据格式
   - ✅ 防止数据泄露

3. **Storage 安全规则**
   - ✅ 限制文件大小（5 MB）
   - ✅ 限制文件类型
   - ✅ 防止恶意上传

## 🚨 故障排查

### 问题 1：Firebase 初始化失败

```
Error: Failed to initialize Firebase
```

**解决方案**：
1. 检查环境变量是否正确设置
2. 验证服务账号 JSON 格式
3. 确认 Firebase 项目已启用 Firestore 和 Storage

### 问题 2：图片上传失败

```
Error: Failed to upload image
```

**解决方案**：
1. 检查 Storage Bucket 名称是否正确
2. 验证服务账号权限
3. 确认图片大小不超过限制

### 问题 3：Clover 同步失败

```
Error: Clover API not configured
```

**解决方案**：
1. 确认 `CLOVER_API_KEY` 和 `MERCHANT_ID` 已设置
2. 检查 Clover API 连接状态
3. 查看日志获取详细错误信息

## 📝 下一步

1. ✅ 集成 Firebase 到 `app_server.py`
2. ✅ 添加前端 UI 支持图片上传
3. ✅ 实现批量导入功能
4. ✅ 添加图片预览和编辑
5. ✅ 部署到 Cloud Run

## 📞 支持

如有问题，请查看：
- [Firebase 文档](https://firebase.google.com/docs)
- [Firestore 指南](https://firebase.google.com/docs/firestore)
- [Cloud Storage 指南](https://firebase.google.com/docs/storage)
