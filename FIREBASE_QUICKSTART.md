# Firebase 快速开始指南

## 🚀 5分钟快速集成

### 步骤 1：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2：配置 Firebase

#### 2.1 创建 Firebase 项目

1. 访问 https://console.firebase.google.com/
2. 选择项目 `stockwise-486801`
3. 启用 **Firestore Database** 和 **Cloud Storage**

#### 2.2 下载服务账号密钥

1. 项目设置 → 服务账号 → 生成新的私钥
2. 保存为 `serviceAccountKey.json`
3. 放在项目根目录

### 步骤 3：配置环境变量

编辑 `.env` 文件：

```bash
FIREBASE_SERVICE_ACCOUNT_PATH=D:/stockwise_final/serviceAccountKey.json
FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com
```

### 步骤 4：测试集成

```bash
python test_firebase_integration.py
```

如果看到 "🎉 All tests passed!"，说明配置成功！

### 步骤 5：启动应用

```bash
uvicorn app_server:app --reload
```

访问 http://localhost:8080/docs 查看 Firebase API 文档。

## 📝 核心 API 使用示例

### 创建商品

```bash
curl -X POST http://localhost:8080/api/firebase/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "苹果",
    "price": 5.99,
    "stock_quantity": 100,
    "category": "水果",
    "description": "新鲜红富士苹果"
  }'
```

### 上传商品图片

```bash
curl -X POST http://localhost:8080/api/firebase/products/{product_id}/image \
  -F "image=@apple.jpg"
```

### 获取商品列表

```bash
# 获取所有商品
curl http://localhost:8080/api/firebase/products?limit=50

# 按分类筛选
curl http://localhost:8080/api/firebase/products?category=水果

# 搜索商品
curl http://localhost:8080/api/firebase/products?search=苹果
```

### 从 Clover 同步商品

```bash
curl -X POST http://localhost:8080/api/firebase/sync-clover
```

## 🎯 完整功能列表

### ✅ Firestore 数据库
- 创建、读取、更新、删除商品
- 按分类筛选
- 商品搜索
- 分页加载
- 统计信息

### ✅ Cloud Storage
- 图片上传（自动压缩）
- 图片删除
- 公开 URL 生成

### ✅ Clover 集成
- 从 Clover API 同步商品
- 智能去重
- 增量同步

## 📊 数据模型

### Firestore 商品文档

```javascript
{
  id: "auto_generated_id",
  name: "商品名称",
  price: 29.99,
  stock_quantity: 100,
  category: "分类",
  description: "描述",
  sku: "SKU-123",
  code: "BARCODE",
  imageUrl: "https://storage.googleapis.com/...",
  created_at: "2026-03-10T16:00:00",
  updated_at: "2026-03-10T16:00:00"
}
```

## 🔧 常见问题

### Q: Firebase 初始化失败？

**A:** 检查环境变量是否正确设置：
```bash
echo $FIREBASE_SERVICE_ACCOUNT_PATH
echo $FIREBASE_STORAGE_BUCKET
```

### Q: 图片上传失败？

**A:** 确认：
1. Storage Bucket 名称正确
2. 服务账号有权限
3. 图片大小 < 5MB

### Q: Clover 同步失败？

**A:** 确认：
1. `CLOVER_API_KEY` 已设置
2. `MERCHANT_ID` 已设置
3. Clover API 可访问

## 📚 更多文档

- **完整设置指南**: `FIREBASE_SETUP.md`
- **部署指南**: `FIREBASE_DEPLOYMENT.md`
- **API 文档**: http://localhost:8080/docs

## 🎉 下一步

1. ✅ 从 Clover 同步商品
2. ✅ 为商品添加分类和描述
3. ✅ 上传商品图片
4. ✅ 部署到 Cloud Run
5. ✅ 配置生产环境安全规则

## 💡 提示

- 图片会自动压缩到 1200x1200，85% 质量
- 使用分页加载避免一次性加载过多数据
- 定期备份 Firestore 数据
- 监控 Firebase 使用量避免超出免费额度
