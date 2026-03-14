# Clover Webhook 集成设置指南

## 📋 概述

本指南介绍如何配置 Clover POS 系统的 Webhook，使其在顾客支付时自动向 Firebase Cloud Functions 发送事件，从而实现积分自动发放。

## 🎯 工作流程

```
顾客支付 (Clover POS)
    ↓
Clover 发送 PAYMENT_PROCESSED 事件
    ↓
Firebase Cloud Function (cloverWebhook)
    ↓
验证签名 → 提取手机号和金额 → 查询会员 → 计算积分 → 更新 Firestore
    ↓
积分自动发放完成
```

## 🚀 部署步骤

### 步骤 1: 部署 Firebase Cloud Functions

```bash
# 1. 进入 functions 目录
cd d:\stockwise_final\functions

# 2. 安装依赖
npm install

# 3. 配置 Clover App Secret（稍后获取）
firebase functions:config:set clover.app_secret="YOUR_CLOVER_APP_SECRET"

# 4. 部署函数
firebase deploy --only functions

# 5. 记录函数 URL
# 输出示例：
# ✔ functions[cloverWebhook(us-central1)]: Successful create operation.
# Function URL: https://us-central1-eastern-market-members.cloudfunctions.net/cloverWebhook
```

**记录你的 Webhook URL**:
```
https://us-central1-eastern-market-members.cloudfunctions.net/cloverWebhook
```

### 步骤 2: 配置 Clover App

#### 2.1 登录 Clover Dashboard

1. 访问: https://www.clover.com/dashboard
2. 使用你的 Clover 账号登录

#### 2.2 创建或选择 App

**选项 A: 创建新 App**
1. 进入 **Apps & Integrations** → **Create App**
2. 填写 App 信息:
   - **App Name**: Eastern Market Points System
   - **Description**: 自动积分发放系统
   - **Category**: Loyalty
3. 点击 **Create**

**选项 B: 使用现有 App**
1. 进入 **Apps & Integrations**
2. 选择你的现有 App

#### 2.3 配置 Webhook

1. 在 App 设置中，找到 **Webhooks** 部分
2. 点击 **Add Webhook**
3. 配置 Webhook:
   - **URL**: 粘贴步骤 1 中记录的函数 URL
   - **Events**: 勾选 **PAYMENT_PROCESSED**
   - **Version**: 选择最新版本（通常是 v3）
4. 点击 **Save**

#### 2.4 获取 App Secret

1. 在 App 设置中，找到 **App Secret** 或 **Credentials**
2. 复制 **App Secret** 值
3. 配置到 Firebase:

```bash
firebase functions:config:set clover.app_secret="YOUR_ACTUAL_APP_SECRET"

# 重新部署以应用配置
firebase deploy --only functions:cloverWebhook
```

#### 2.5 配置权限

确保 App 拥有以下权限:
- **Read Customers** - 读取顾客信息（包括手机号）
- **Read Orders** - 读取订单信息
- **Read Payments** - 读取支付信息

### 步骤 3: 测试 Webhook

#### 3.1 在 Clover 测试环境测试

1. 登录 Clover Sandbox: https://sandbox.dev.clover.com/
2. 创建测试订单
3. 添加顾客信息（包含手机号）
4. 完成支付
5. 检查 Firebase Functions 日志:

```bash
firebase functions:log --only cloverWebhook
```

#### 3.2 使用 curl 测试

```bash
# 模拟 Clover webhook 请求
curl -X POST https://us-central1-eastern-market-members.cloudfunctions.net/cloverWebhook \
  -H "Content-Type: application/json" \
  -H "x-clover-signature: test_signature" \
  -d '{
    "type": "PAYMENT_PROCESSED",
    "payment": {
      "id": "TEST123",
      "amount": 5000,
      "customer": {
        "phoneNumbers": [
          {"phoneNumber": "+16131234567"}
        ]
      }
    }
  }'
```

**注意**: 实际测试需要使用真实的 Clover 签名。

## 📱 Clover POS 配置

### 在 POS 设备上收集手机号

为了让系统能够识别会员并发放积分，需要在支付时收集顾客手机号。

#### 方法 1: 使用 Clover Customer Management

1. 在 Clover POS 上，进入 **Customers**
2. 添加或编辑顾客信息
3. 确保填写 **Phone Number** 字段
4. 在结账时选择该顾客

#### 方法 2: 在结账时添加顾客

1. 在结账界面，点击 **Add Customer**
2. 输入手机号（格式：+1XXXXXXXXXX 或 XXXXXXXXXX）
3. 完成支付

#### 方法 3: 使用自定义 Tender

如果需要更灵活的方式，可以创建自定义 Tender 来收集手机号。

## 🔍 验证集成

### 检查清单

- [ ] Firebase Cloud Functions 已部署
- [ ] Clover App 已创建并配置
- [ ] Webhook URL 已添加到 Clover
- [ ] PAYMENT_PROCESSED 事件已勾选
- [ ] App Secret 已配置到 Firebase
- [ ] App 权限已正确设置
- [ ] 测试支付已成功触发 webhook
- [ ] Firebase 日志显示成功处理
- [ ] Firestore 中积分已正确更新

### 验证步骤

#### 1. 检查 Firebase Functions 状态

```bash
firebase functions:list
```

应该看到:
```
cloverWebhook(us-central1)
csvImport(us-central1)
validateCSV(us-central1)
manualAddPoints(us-central1)
```

#### 2. 查看实时日志

```bash
firebase functions:log --only cloverWebhook --follow
```

#### 3. 测试完整流程

1. 在 Firestore 创建测试会员:
   ```javascript
   // members 集合
   {
     name: "测试会员",
     phone: "+16131234567",
     email: "test@example.com",
     totalPoints: 0,
     lifetimePoints: 0,
     tier: "bronze",
     isActive: true
   }
   ```

2. 在 Clover POS 创建订单:
   - 添加商品（总价 $50.00）
   - 添加顾客（手机号 +16131234567）
   - 完成支付

3. 检查结果:
   - Firebase 日志应显示成功处理
   - Firestore `members` 集合中积分应增加 50
   - Firestore `points_transactions` 应有新记录

## 🔧 故障排除

### 问题 1: Webhook 未触发

**可能原因**:
- Webhook URL 配置错误
- 事件类型未勾选
- Clover App 未激活

**解决方案**:
1. 检查 Clover Dashboard 中的 Webhook 配置
2. 确认 URL 完全正确（包括 https://）
3. 确认 PAYMENT_PROCESSED 已勾选
4. 检查 App 状态是否为 Active

### 问题 2: 签名验证失败

**症状**: 日志显示 "Invalid Clover signature"

**解决方案**:
1. 检查 App Secret 是否正确配置:
   ```bash
   firebase functions:config:get
   ```
2. 确认 App Secret 与 Clover Dashboard 中一致
3. 重新部署函数:
   ```bash
   firebase deploy --only functions:cloverWebhook
   ```

### 问题 3: 会员未找到

**症状**: 日志显示 "Member not found"

**解决方案**:
1. 检查 Firestore `members` 集合
2. 确认手机号格式为 +1XXXXXXXXXX
3. 确认 Clover 发送的手机号格式
4. 查看日志中提取的手机号:
   ```bash
   firebase functions:log --only cloverWebhook | grep "phone="
   ```

### 问题 4: 积分计算错误

**症状**: 积分数量不符合预期

**解决方案**:
1. 检查会员等级（Bronze/Silver/Gold）
2. 验证倍率计算:
   - Bronze: 1.0x
   - Silver: 1.5x
   - Gold: 2.0x
3. 检查金额单位（Clover 使用分，需要除以 100）

## 📊 监控和维护

### 设置告警

在 Firebase Console 设置告警:
1. 进入 **Functions** → **Logs**
2. 点击 **Create Alert**
3. 配置条件:
   - 错误率 > 5%
   - 执行时间 > 30 秒
4. 设置通知方式（邮件/SMS）

### 定期检查

建议每周检查:
- [ ] Webhook 触发次数
- [ ] 成功率
- [ ] 平均响应时间
- [ ] 错误日志

### 日志查询

```bash
# 查看最近 1 小时的日志
firebase functions:log --only cloverWebhook --since 1h

# 查看错误日志
firebase functions:log --only cloverWebhook | grep ERROR

# 查看特定手机号的处理
firebase functions:log --only cloverWebhook | grep "+16131234567"
```

## 🔒 安全最佳实践

### 1. 保护 App Secret

- ✅ 使用 Firebase Functions Config 存储
- ✅ 不要提交到 Git
- ✅ 定期轮换密钥
- ❌ 不要硬编码在代码中

### 2. 验证所有请求

- ✅ 始终验证 Clover 签名
- ✅ 检查请求来源
- ✅ 验证数据格式

### 3. 限制访问

- ✅ 使用 Firestore Security Rules
- ✅ 只允许 Cloud Functions 写入积分
- ✅ 管理员功能需要权限验证

## 📞 支持和联系

### 相关资源

- **Clover 文档**: https://docs.clover.com/docs/webhooks
- **Firebase 文档**: https://firebase.google.com/docs/functions
- **项目文档**: `functions/README.md`

### 联系信息

- **项目**: StockWise - Eastern Market
- **Firebase 项目**: eastern-market-members
- **账号**: easternmarketsask@gmail.com

## 🎉 完成！

恭喜！你已经成功配置了 Clover Webhook 集成。现在每次顾客在 Clover POS 支付时，系统会自动:

1. ✅ 接收支付事件
2. ✅ 验证请求签名
3. ✅ 提取顾客手机号和消费金额
4. ✅ 查询会员信息
5. ✅ 根据等级计算积分（含倍率）
6. ✅ 原子更新 Firestore
7. ✅ 自动升级会员等级（如适用）

积分系统现已全自动运行！🚀
