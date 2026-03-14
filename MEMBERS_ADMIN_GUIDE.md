# 会员管理模块使用指南

## 📋 概述

会员管理模块已成功集成到 StockWise 后台管理系统中，提供完整的会员数据管理、积分调整和批量导入功能。

**项目信息：**
- **数据源**: Firebase eastern-market-members 项目
- **访问方式**: StockWise 后台 → 👥 会员管理标签
- **认证方式**: X-Admin-Token header

---

## 🎯 功能模块

### 模块 1: 数据统计卡片

**位置**: 页面顶部横排

**显示内容**:
- **总会员数**: 所有注册会员总数
- **本月新增**: 当月新注册会员数
- **本月积分发放**: 当月发放积分总数（需要交易数据）
- **活跃会员数**: 拥有积分的会员数量

**数据来源**: `GET /api/members/list`

**自动更新**: 每次切换到会员管理标签时自动加载

---

### 模块 2: 会员列表

**功能**:
- 搜索会员（按姓名或手机号）
- 显示会员基本信息表格
- 点击"查看"按钮打开会员详情弹窗

**表格列**:
| 列名 | 说明 | 示例 |
|------|------|------|
| 姓名 | 会员姓名 | 张三 |
| 手机号 | 电话号码 | +13065551234 |
| 等级 | 会员等级徽章 | 铜牌/银牌/金牌 |
| 积分 | 当前积分余额 | 500 |
| 注册日期 | 加入日期 | 2026-03-01 |
| 操作 | 查看按钮 | [查看] |

**搜索功能**:
- 空搜索：加载前 100 位会员（按积分排序）
- 姓名搜索：模糊匹配会员姓名
- 手机号搜索：精确匹配（自动标准化格式）

**API 端点**: `GET /api/members/list?search={keyword}&limit=100`

---

### 模块 3: 会员详情弹窗

**打开方式**: 点击会员列表中的"查看"按钮

**左侧 - 基本信息**:
- 姓名
- 手机号
- 会员等级（铜牌/银牌/金牌）
- 当前积分
- 注册日期

**右侧 - 手动调整积分**:
- **积分变动输入框**: 正数加分，负数扣分
- **操作备注**: 必填，记录调整原因
- **确认调整按钮**: 提交积分调整

**底部 - 积分历史**:
- 显示最近 10 条积分交易记录
- 包含：类型、积分、说明、时间
- 类型标签：获得、兑换、调整、注册奖励

**API 端点**:
- 会员详情: `GET /api/members/list` (从列表中查找)
- 积分历史: `GET /api/members/{member_id}/points-history?limit=10`
- 调整积分: `POST /api/members/{member_id}/adjust-points`

**调整积分请求体**:
```json
{
  "points": 100,
  "staff_note": "补偿积分",
  "admin_uid": "admin"
}
```

**成功后**:
- 显示绿色成功提示
- 自动刷新会员详情和积分历史
- 1秒后刷新会员列表

---

### 模块 4: CSV 批量导入积分

**CSV 格式要求**:
```csv
date,amount,phone,order_id
2026-03-14,50.00,3065551234,ORDER123
2026-03-14,100.00,3065555678,ORDER124
```

**字段说明**:
- `date`: 日期（可选）
- `amount`: 消费金额（必填）
- `phone`: 手机号（必填，10位数字）
- `order_id`: 订单ID（可选）

**导入流程**:

1. **选择文件**: 点击"选择 CSV 文件"
2. **上传预览**: 点击"📤 上传并预览"
   - 显示将处理的行数
   - 显示预计匹配的会员数
3. **确认导入**: 点击"✅ 确认导入"
   - 开始批量处理
   - 显示进度和结果
4. **查看结果**:
   - 成功条数
   - 失败条数
   - 失败明细表格（行号、手机号、失败原因）

**积分计算规则**:
- 默认：$1 = 10 积分
- 可在 `app_server.py` 第 4311 行修改

**API 端点**: `POST /api/members/bulk-points`

**失败原因示例**:
- "Missing amount or phone" - 缺少必填字段
- "Invalid amount: xxx" - 金额格式错误
- "Member not found" - 未找到会员
- "Failed to add points" - 积分添加失败

---

## 🔒 安全配置

### Admin Token 配置

**当前配置**: `app_server.py` 第 3122 行
```javascript
const ADMIN_TOKEN = 'your-admin-token-here'; // TODO: Replace with actual admin token
```

**修改步骤**:
1. 在 `secure_config.py` 中设置 admin token
2. 更新 JavaScript 中的 `ADMIN_TOKEN` 常量
3. 确保所有 API 请求都携带正确的 token

**验证机制**: 
- 所有会员管理 API 都需要 `X-Admin-Token` header
- 服务端通过 `verify_admin_token()` 验证
- 无效 token 返回 403 Forbidden

---

## 📊 API 端点总览

### 1. 获取会员列表
```http
GET /api/members/list?search={keyword}&limit={limit}
Headers: X-Admin-Token: {token}
```

**响应**:
```json
{
  "members": [
    {
      "uid": "abc123",
      "name": "张三",
      "phone": "+13065551234",
      "tier": "bronze",
      "totalPoints": 500,
      "joinDate": "2026-03-01"
    }
  ],
  "count": 1
}
```

### 2. 获取积分历史
```http
GET /api/members/{member_id}/points-history?limit={limit}
Headers: X-Admin-Token: {token}
```

**响应**:
```json
{
  "transactions": [
    {
      "id": "tx123",
      "memberId": "abc123",
      "type": "earn",
      "points": 100,
      "description": "购物消费 $10.00 获得积分",
      "source": "clover",
      "createdAt": "2026-03-14T10:30:00Z"
    }
  ],
  "count": 1
}
```

### 3. 手动调整积分
```http
POST /api/members/{member_id}/adjust-points
Headers: 
  X-Admin-Token: {token}
  Content-Type: application/json
Body:
{
  "points": 100,
  "staff_note": "补偿积分",
  "admin_uid": "admin"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Points adjusted by 100"
}
```

### 4. 批量导入积分
```http
POST /api/members/bulk-points
Headers: X-Admin-Token: {token}
Body: multipart/form-data
  file: {csv_file}
```

**响应**:
```json
{
  "total": 10,
  "success": 8,
  "failed": 2,
  "failed_rows": [
    {
      "row": 3,
      "phone": "3065551234",
      "reason": "Member not found"
    }
  ]
}
```

---

## 🎨 UI 样式说明

**设计风格**: 与现有 StockWise 后台保持一致

**颜色方案**:
- 主色调: `#1e63d2` (蓝色)
- 成功: `#2e7d32` (绿色)
- 警告: `#b26b00` (橙色)
- 错误: `#b42318` (红色)
- 背景: `#f6f8fc` (浅灰)

**组件复用**:
- `.card` - 卡片容器
- `.btn` - 主按钮
- `.btn.secondary` - 次要按钮
- `.status` - 状态提示
- `.badge` - 徽章标签
- `.prod-modal-overlay` - 弹窗遮罩

**响应式设计**:
- 桌面端: 完整表格和双列布局
- 移动端: 自适应单列布局

---

## 🔧 技术实现

### 前端技术
- **框架**: 原生 JavaScript (无依赖)
- **样式**: 内联 CSS (与现有系统一致)
- **数据获取**: Fetch API
- **文件处理**: FileReader API

### 后端技术
- **框架**: FastAPI
- **数据库**: Firebase Firestore (eastern-market-members)
- **认证**: Header-based token
- **文件处理**: Python csv module

### 数据流
```
前端 JavaScript
  ↓ (Fetch + X-Admin-Token)
FastAPI 端点 (/api/members/*)
  ↓ (verify_admin_token)
member_connector.py
  ↓ (Firebase Admin SDK)
Firebase Firestore (eastern-market-members)
```

---

## 🐛 故障排除

### 问题 1: "搜索失败: 401 Unauthorized"
**原因**: Admin token 未配置或错误
**解决**: 更新 `ADMIN_TOKEN` 常量为正确的 token

### 问题 2: "会员数据未加载"
**原因**: Firebase 连接失败
**解决**: 
1. 检查 `serviceAccountKey_members.json` 是否存在
2. 确认 Firebase 项目 ID 正确
3. 查看服务器日志

### 问题 3: "CSV 导入失败"
**原因**: CSV 格式错误或会员不存在
**解决**:
1. 检查 CSV 格式是否正确（逗号分隔）
2. 确认手机号格式（10位数字）
3. 查看失败明细表格

### 问题 4: "积分调整失败"
**原因**: 积分不足或数据验证失败
**解决**:
1. 检查会员当前积分余额
2. 确认备注已填写
3. 查看错误提示信息

---

## 📝 开发备注

### 待优化项
1. **本月积分发放统计**: 需要查询交易数据计算
2. **Admin Token 管理**: 建议使用环境变量或密钥管理
3. **批量导入进度条**: 可添加实时进度显示
4. **会员详情缓存**: 避免重复请求

### 扩展建议
1. **导出功能**: 导出会员列表为 CSV
2. **高级筛选**: 按等级、积分范围筛选
3. **批量操作**: 批量调整积分
4. **操作日志**: 记录所有管理员操作

---

## 📞 技术支持

**项目路径**: `d:\stockwise_final`
**主文件**: `app_server.py`
**会员连接器**: `member_connector.py`
**Firebase 项目**: eastern-market-members

**相关文档**:
- `MEMBER_INTEGRATION.md` - 会员系统集成文档
- `README.md` - StockWise 项目说明

---

## ✅ 部署检查清单

- [ ] 更新 `ADMIN_TOKEN` 为实际 token
- [ ] 确认 `serviceAccountKey_members.json` 已配置
- [ ] 测试会员列表加载
- [ ] 测试会员详情弹窗
- [ ] 测试积分调整功能
- [ ] 测试 CSV 批量导入
- [ ] 验证所有 API 端点
- [ ] 检查错误处理和提示
- [ ] 测试响应式布局
- [ ] 部署到生产环境

---

**文档版本**: 1.0  
**创建日期**: 2026-03-14  
**最后更新**: 2026-03-14
