# Firebase 部署指南

## 📦 部署前准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖：
- `firebase-admin>=6.5.0`
- `Pillow>=10.0.0`
- `python-multipart>=0.0.6`

### 2. Firebase 项目配置

#### 创建 Firebase 项目

1. 访问 [Firebase Console](https://console.firebase.google.com/)
2. 选择现有项目 `stockwise-486801` 或创建新项目
3. 启用以下服务：
   - **Firestore Database**
   - **Cloud Storage**

#### 配置 Firestore

1. 进入 Firestore Database
2. 选择 **生产模式** 启动
3. 选择区域：`us-central1`（与 Cloud Run 相同）
4. 创建数据库

#### 配置 Cloud Storage

1. 进入 Cloud Storage
2. 创建 bucket（如果不存在）：`stockwise-486801.appspot.com`
3. 选择区域：`us-central1`

### 3. 配置安全规则

#### Firestore 安全规则

在 Firestore Console → 规则中设置：

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 商品集合
    match /products/{productId} {
      // 允许所有人读取
      allow read: if true;
      
      // 只允许认证用户写入
      allow write: if request.auth != null;
    }
  }
}
```

**临时开发规则（仅用于测试）：**

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;  // 警告：仅用于开发测试！
    }
  }
}
```

#### Cloud Storage 安全规则

在 Storage Console → 规则中设置：

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // 商品图片文件夹
    match /products/{imageId} {
      // 允许所有人读取
      allow read: if true;
      
      // 只允许认证用户上传，限制文件大小 5MB
      allow write: if request.auth != null 
                   && request.resource.size < 5 * 1024 * 1024
                   && request.resource.contentType.matches('image/.*');
    }
  }
}
```

**临时开发规则（仅用于测试）：**

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if true;  // 警告：仅用于开发测试！
    }
  }
}
```

### 4. 获取服务账号密钥

#### 方式 A：下载 JSON 密钥文件

1. Firebase Console → 项目设置 → 服务账号
2. 点击 **生成新的私钥**
3. 下载 `serviceAccountKey.json`
4. **重要：不要提交到 Git！**

#### 方式 B：使用 Google Cloud 服务账号

```bash
# 创建服务账号
gcloud iam service-accounts create stockwise-firebase \
    --display-name="StockWise Firebase Service Account"

# 授予权限
gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:stockwise-firebase@stockwise-486801.iam.gserviceaccount.com" \
    --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:stockwise-firebase@stockwise-486801.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:stockwise-firebase@stockwise-486801.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# 生成密钥
gcloud iam service-accounts keys create serviceAccountKey.json \
    --iam-account=stockwise-firebase@stockwise-486801.iam.gserviceaccount.com
```

## 🖥️ 本地开发部署

### 1. 配置环境变量

编辑 `.env` 文件：

```bash
# Clover API
CLOVER_API_KEY=your_clover_api_key
MERCHANT_ID=your_merchant_id

# AI APIs (可选)
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_anthropic_key

# Firebase - 使用本地密钥文件
FIREBASE_SERVICE_ACCOUNT_PATH=D:/stockwise_final/serviceAccountKey.json
FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com
```

### 2. 启动应用

```bash
# 方式 1：直接运行
python -m uvicorn app_server:app --host 0.0.0.0 --port 8080 --reload

# 方式 2：使用 uvicorn 命令
uvicorn app_server:app --reload
```

### 3. 测试 Firebase 功能

访问 `http://localhost:8080/docs` 查看 API 文档，测试以下端点：

```bash
# 获取统计信息
curl http://localhost:8080/api/firebase/statistics

# 创建商品
curl -X POST http://localhost:8080/api/firebase/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试商品",
    "price": 29.99,
    "stock_quantity": 100,
    "category": "测试分类"
  }'

# 从 Clover 同步商品
curl -X POST http://localhost:8080/api/firebase/sync-clover
```

## ☁️ Cloud Run 部署

### 方式 1：使用服务账号 JSON 字符串

#### 1. 准备 JSON 字符串

```bash
# 将 JSON 文件压缩为单行
cat serviceAccountKey.json | jq -c . > serviceAccountKey-oneline.json

# 或使用 Python
python -c "import json; print(json.dumps(json.load(open('serviceAccountKey.json'))))"
```

#### 2. 部署到 Cloud Run

```bash
# 读取 JSON 内容
FIREBASE_JSON=$(cat serviceAccountKey-oneline.json)

# 部署应用
gcloud run deploy stockwise-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="CLOVER_API_KEY=your_key" \
  --set-env-vars="MERCHANT_ID=your_id" \
  --set-env-vars="FIREBASE_SERVICE_ACCOUNT_JSON=${FIREBASE_JSON}" \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com" \
  --memory 1Gi \
  --timeout 300 \
  --max-instances 10
```

### 方式 2：使用 Secret Manager（推荐）

#### 1. 创建 Secret

```bash
# 创建 Secret
gcloud secrets create firebase-service-account \
    --data-file=serviceAccountKey.json \
    --replication-policy="automatic"

# 授予 Cloud Run 访问权限
gcloud secrets add-iam-policy-binding firebase-service-account \
    --member="serviceAccount:873982544406-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### 2. 部署应用

```bash
gcloud run deploy stockwise-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="CLOVER_API_KEY=your_key" \
  --set-env-vars="MERCHANT_ID=your_id" \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com" \
  --set-secrets="FIREBASE_SERVICE_ACCOUNT_JSON=firebase-service-account:latest" \
  --memory 1Gi \
  --timeout 300
```

### 方式 3：使用 Cloud Run 默认服务账号

如果 Cloud Run 服务账号已有 Firebase 权限，可以使用默认凭据：

```bash
# 授予 Cloud Run 服务账号 Firebase 权限
gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:873982544406-compute@developer.gserviceaccount.com" \
    --role="roles/firebase.admin"

gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:873982544406-compute@developer.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:873982544406-compute@developer.gserviceaccount.com" \
    --role="roles/storage.admin"

# 部署（不需要 FIREBASE_SERVICE_ACCOUNT_JSON）
gcloud run deploy stockwise-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="CLOVER_API_KEY=your_key" \
  --set-env-vars="MERCHANT_ID=your_id" \
  --set-env-vars="FIREBASE_STORAGE_BUCKET=stockwise-486801.appspot.com" \
  --memory 1Gi
```

## 🔍 验证部署

### 1. 检查日志

```bash
# 查看最新日志
gcloud run services logs read stockwise-app --region us-central1 --limit 50

# 实时查看日志
gcloud run services logs tail stockwise-app --region us-central1
```

查找以下日志确认 Firebase 已启用：

```
INFO:startup:FIREBASE_ENABLED: True
INFO:root:Firebase API endpoints enabled
INFO:root:Firebase initialized successfully
```

### 2. 测试 API 端点

```bash
# 获取服务 URL
SERVICE_URL=$(gcloud run services describe stockwise-app --region us-central1 --format 'value(status.url)')

# 测试 Firebase 统计
curl ${SERVICE_URL}/api/firebase/statistics

# 测试创建商品
curl -X POST ${SERVICE_URL}/api/firebase/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "云端测试商品",
    "price": 19.99,
    "category": "测试"
  }'

# 测试获取商品列表
curl ${SERVICE_URL}/api/firebase/products?limit=10
```

### 3. 验证 Firestore 数据

1. 访问 [Firestore Console](https://console.firebase.google.com/)
2. 选择项目 `stockwise-486801`
3. 进入 Firestore Database
4. 查看 `products` 集合是否有数据

### 4. 验证 Cloud Storage

1. 访问 [Storage Console](https://console.firebase.google.com/)
2. 选择项目 `stockwise-486801`
3. 进入 Cloud Storage
4. 查看 `products/` 文件夹是否有图片

## 🔧 故障排查

### 问题 1：Firebase 初始化失败

**错误信息：**
```
ERROR: Failed to initialize Firebase
```

**解决方案：**

1. 检查环境变量：
```bash
gcloud run services describe stockwise-app --region us-central1 --format yaml | grep -A 20 "env:"
```

2. 验证服务账号 JSON 格式：
```bash
# 本地测试
python -c "import json; json.load(open('serviceAccountKey.json'))"
```

3. 检查权限：
```bash
gcloud projects get-iam-policy stockwise-486801 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*firebase*"
```

### 问题 2：Firestore 权限被拒绝

**错误信息：**
```
PERMISSION_DENIED: Missing or insufficient permissions
```

**解决方案：**

1. 更新安全规则为开发模式（临时）
2. 检查服务账号权限：
```bash
gcloud projects add-iam-policy-binding stockwise-486801 \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
    --role="roles/datastore.user"
```

### 问题 3：图片上传失败

**错误信息：**
```
Failed to upload image
```

**解决方案：**

1. 检查 Storage Bucket 名称
2. 验证服务账号有 Storage Admin 权限
3. 检查安全规则是否允许写入
4. 确认文件大小不超过 5MB

### 问题 4：Cloud Run 内存不足

**错误信息：**
```
Memory limit exceeded
```

**解决方案：**

增加内存限制：
```bash
gcloud run services update stockwise-app \
  --region us-central1 \
  --memory 2Gi
```

## 📊 监控和日志

### 启用详细日志

在 `firebase_config.py` 中添加：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Cloud Run 指标

访问 [Cloud Run Console](https://console.cloud.google.com/run) 查看：
- 请求数量
- 响应时间
- 错误率
- 内存使用
- CPU 使用

### Firestore 使用情况

访问 [Firestore Console](https://console.firebase.google.com/) → 使用情况：
- 读取次数
- 写入次数
- 删除次数
- 存储大小

### Storage 使用情况

访问 [Storage Console](https://console.firebase.google.com/) → 使用情况：
- 存储大小
- 下载流量
- 操作次数

## 🔒 安全最佳实践

### 1. 保护服务账号密钥

```bash
# 添加到 .gitignore
echo "serviceAccountKey.json" >> .gitignore
echo "serviceAccountKey-oneline.json" >> .gitignore

# 使用 Secret Manager
gcloud secrets create firebase-service-account --data-file=serviceAccountKey.json
```

### 2. 限制 CORS

在 `app_server.py` 中更新：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 3. 启用认证

添加 Firebase Authentication：

```python
from firebase_admin import auth

def verify_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 4. 限流

使用 Cloud Armor 或添加速率限制：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/firebase/products")
@limiter.limit("10/minute")
async def create_product(...):
    ...
```

## 📝 维护建议

### 定期备份

```bash
# 导出 Firestore 数据
gcloud firestore export gs://stockwise-486801-backup/firestore-backup

# 备份 Storage
gsutil -m cp -r gs://stockwise-486801.appspot.com gs://stockwise-486801-backup/storage-backup
```

### 清理未使用的图片

定期运行清理脚本删除孤立图片（商品已删除但图片仍存在）。

### 监控成本

设置预算警报：
```bash
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="StockWise Budget" \
  --budget-amount=50USD \
  --threshold-rule=percent=80
```

## 🎯 下一步

1. ✅ 配置 Firebase 项目和安全规则
2. ✅ 部署到 Cloud Run
3. ✅ 测试所有 API 端点
4. ✅ 从 Clover 同步商品数据
5. ✅ 上传商品图片
6. ✅ 配置监控和警报
7. ✅ 实施安全最佳实践
