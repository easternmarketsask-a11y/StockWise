# Firebase Cloud Functions - StockWise 积分管理系统

## 📋 项目概述

这是 StockWise 项目的 Firebase Cloud Functions，用于处理 Clover POS webhook 和批量积分导入。

### 核心功能
1. **Clover Webhook 接收器** - 自动接收支付事件并发放积分
2. **CSV 批量导入** - 批量导入历史交易并发放积分
3. **CSV 格式验证** - 验证 CSV 格式（不实际导入）
4. **手动添加积分** - 管理员手动调整积分

## 📁 文件结构

```
functions/
├── index.js              # 主入口，导出所有 Cloud Functions
├── cloverWebhook.js      # Clover webhook 处理逻辑
├── pointsService.js      # 积分计算和会员等级管理
├── csvImport.js          # CSV 批量导入功能
├── package.json          # 依赖配置
└── README.md            # 本文档
```

## 🎯 积分规则

### 基础规则
- **每 $1 CAD = 1 积分**（基础）

### 会员等级倍率
| 等级 | 累计积分范围 | 倍率 |
|------|-------------|------|
| Bronze | 0 - 999 | 1.0x |
| Silver | 1,000 - 4,999 | 1.5x |
| Gold | 5,000+ | 2.0x |

### 示例
- Bronze 会员消费 $50 → 获得 50 积分
- Silver 会员消费 $50 → 获得 75 积分
- Gold 会员消费 $50 → 获得 100 积分

## 🚀 部署步骤

### 1. 安装依赖

```bash
cd functions
npm install
```

### 2. 配置环境变量

```bash
# 设置 Clover App Secret
firebase functions:config:set clover.app_secret="YOUR_CLOVER_APP_SECRET"

# 查看当前配置
firebase functions:config:get
```

### 3. 部署到 Firebase

```bash
# 部署所有函数
firebase deploy --only functions

# 部署单个函数
firebase deploy --only functions:cloverWebhook
firebase deploy --only functions:csvImport
```

### 4. 查看日志

```bash
# 实时查看日志
firebase functions:log --only cloverWebhook

# 查看所有函数日志
firebase functions:log
```

## 📡 API 端点

### 1. Clover Webhook

**URL**: `https://us-central1-{project-id}.cloudfunctions.net/cloverWebhook`

**Method**: `POST`

**Headers**:
```
x-clover-signature: {signature}
Content-Type: application/json
```

**Request Body** (Clover 自动发送):
```json
{
  "type": "PAYMENT_PROCESSED",
  "payment": {
    "id": "ORDER123",
    "amount": 4550,
    "customer": {
      "phoneNumbers": [
        {"phoneNumber": "+16131234567"}
      ]
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Points added successfully",
  "data": {
    "memberId": "user123",
    "memberName": "张三",
    "phone": "+16131234567",
    "amount": 45.50,
    "pointsAdded": 68,
    "newTotalPoints": 1568,
    "tier": "silver",
    "tierUpgraded": true
  }
}
```

### 2. CSV 批量导入

**URL**: `https://us-central1-{project-id}.cloudfunctions.net/csvImport`

**Method**: `POST`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "csvContent": "date,amount,phone,order_id\n2026-03-01,45.50,+16131234567,ORDER123\n2026-03-02,30.00,+16139876543,ORDER124",
  "adminUid": "admin_user_id"
}
```

**CSV 格式**:
```csv
date,amount,phone,order_id
2026-03-01,45.50,+16131234567,ORDER123
2026-03-02,30.00,+16139876543,ORDER124
2026-03-03,100.00,+16135551234,ORDER125
```

**Response**:
```json
{
  "success": true,
  "message": "CSV import completed",
  "results": {
    "total": 3,
    "success": 2,
    "failed": 1,
    "successRate": "66.67%",
    "errors": [
      {
        "phone": "+16139876543",
        "error": "Member not found"
      }
    ],
    "details": [
      {
        "phone": "+16131234567",
        "memberId": "user123",
        "amount": 45.50,
        "points": 68,
        "tierUpgraded": true
      }
    ]
  }
}
```

### 3. 验证 CSV 格式

**URL**: `https://us-central1-{project-id}.cloudfunctions.net/validateCSV`

**Method**: `POST`

**Request Body**:
```json
{
  "csvContent": "date,amount,phone,order_id\n2026-03-01,45.50,+16131234567,ORDER123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "CSV validation successful",
  "data": {
    "totalRows": 1,
    "sample": [
      {
        "date": "2026-03-01",
        "amount": 45.50,
        "phone": "+16131234567",
        "order_id": "ORDER123"
      }
    ],
    "columns": ["date", "amount", "phone", "order_id"]
  }
}
```

### 4. 手动添加积分

**URL**: `https://us-central1-{project-id}.cloudfunctions.net/manualAddPoints`

**Method**: `POST`

**Request Body**:
```json
{
  "adminUid": "admin_user_id",
  "memberId": "user123",
  "points": 100,
  "reason": "生日奖励"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Points added successfully",
  "data": {
    "success": true,
    "memberId": "user123",
    "pointsAdded": 100,
    "newTotalPoints": 1668,
    "tierUpgraded": false
  }
}
```

## 🔧 配置 Clover Webhook

### 1. 登录 Clover Dashboard
访问: https://www.clover.com/dashboard

### 2. 创建 Webhook
1. 进入 **Apps & Integrations** → **Your App**
2. 点击 **Webhooks**
3. 添加新的 Webhook URL:
   ```
   https://us-central1-{project-id}.cloudfunctions.net/cloverWebhook
   ```
4. 选择事件类型: **PAYMENT_PROCESSED**
5. 保存配置

### 3. 获取 App Secret
1. 在 App 设置中找到 **App Secret**
2. 复制并配置到 Firebase:
   ```bash
   firebase functions:config:set clover.app_secret="YOUR_APP_SECRET"
   ```

## 🔒 安全配置

### Firestore Security Rules

确保 `members` 集合包含 `role` 字段用于管理员验证:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /members/{userId} {
      allow read: if request.auth != null && 
        (request.auth.uid == userId || 
         get(/databases/$(database)/documents/members/$(request.auth.uid)).data.role == 'admin');
      
      allow write: if request.auth != null && 
        get(/databases/$(database)/documents/members/$(request.auth.uid)).data.role == 'admin';
    }
    
    match /points_transactions/{transactionId} {
      allow read: if request.auth != null;
      allow write: if false; // 只能通过 Cloud Functions 写入
    }
  }
}
```

## 🧪 本地测试

### 1. 启动 Firebase Emulator

```bash
firebase emulators:start --only functions
```

### 2. 测试 Clover Webhook

```bash
curl -X POST http://localhost:5001/{project-id}/us-central1/cloverWebhook \
  -H "Content-Type: application/json" \
  -H "x-clover-signature: test_signature" \
  -d '{
    "type": "PAYMENT_PROCESSED",
    "payment": {
      "id": "TEST123",
      "amount": 5000,
      "customer": {
        "phoneNumbers": [{"phoneNumber": "+16131234567"}]
      }
    }
  }'
```

### 3. 测试 CSV 导入

```bash
curl -X POST http://localhost:5001/{project-id}/us-central1/csvImport \
  -H "Content-Type: application/json" \
  -d '{
    "csvContent": "date,amount,phone,order_id\n2026-03-01,45.50,+16131234567,ORDER123",
    "adminUid": "admin_user_id"
  }'
```

## 📊 监控和日志

### 查看实时日志

```bash
# 所有函数
firebase functions:log

# 特定函数
firebase functions:log --only cloverWebhook

# 过滤错误
firebase functions:log --only cloverWebhook | grep ERROR
```

### Firebase Console

访问 Firebase Console 查看详细监控:
- **Functions Dashboard**: https://console.firebase.google.com/project/{project-id}/functions
- **Logs**: https://console.firebase.google.com/project/{project-id}/functions/logs

## ⚠️ 注意事项

### 1. 手机号格式
- 所有手机号自动标准化为 `+1XXXXXXXXXX` 格式
- 支持输入格式: `+16131234567`, `6131234567`, `(613) 123-4567`

### 2. 积分计算
- 积分向下取整（例如：$45.50 × 1.5 = 68.25 → 68 积分）
- 等级升级基于 `lifetimePoints`（累计获得积分）
- 等级降级不会自动发生

### 3. 错误处理
- Webhook 总是返回 200 状态码，避免 Clover 重试
- 错误信息记录在日志中
- CSV 导入失败的行会在 `errors` 数组中返回

### 4. 性能限制
- `cloverWebhook`: 60 秒超时，256MB 内存
- `csvImport`: 540 秒超时（最大值），512MB 内存
- 大批量导入建议分批处理（每批 < 1000 条）

## 🔄 更新和维护

### 更新函数代码

```bash
# 1. 修改代码
# 2. 重新部署
firebase deploy --only functions

# 3. 验证部署
firebase functions:log --only cloverWebhook
```

### 回滚到之前版本

```bash
# 查看部署历史
firebase functions:list

# 回滚（通过重新部署之前的代码）
git checkout <previous-commit>
firebase deploy --only functions
```

## 📞 故障排除

### 问题 1: Webhook 签名验证失败

**症状**: 返回 401 Invalid signature

**解决方案**:
1. 检查 `clover.app_secret` 配置是否正确
2. 确认 Clover App Secret 没有变化
3. 查看日志确认签名计算逻辑

### 问题 2: 会员未找到

**症状**: 返回 "Member not found"

**解决方案**:
1. 确认手机号格式正确（+1XXXXXXXXXX）
2. 检查 Firestore `members` 集合中是否存在该会员
3. 确认 `phone` 字段匹配

### 问题 3: CSV 导入超时

**症状**: 函数执行超过 540 秒

**解决方案**:
1. 减少单次导入的数据量（< 1000 条）
2. 分批导入
3. 考虑使用后台任务处理大批量数据

## 📚 相关文档

- [Firebase Cloud Functions 文档](https://firebase.google.com/docs/functions)
- [Clover Webhook 文档](https://docs.clover.com/docs/webhooks)
- [StockWise 会员系统文档](../MEMBER_INTEGRATION.md)

## 📧 联系信息

- **项目**: StockWise - Eastern Market
- **Firebase 项目**: eastern-market-members
- **账号**: easternmarketsask@gmail.com
