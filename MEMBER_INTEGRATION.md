# StockWise 会员系统集成文档

## 📋 概述

`member_connector.py` 模块连接 StockWise 与 Firebase 会员系统，实现积分管理、会员查询等功能。

## 🔧 配置要求

### 1. 服务账号密钥
在 StockWise 项目根目录放置 `serviceAccountKey_members.json`：

```bash
d:\stockwise_final\
├── member_connector.py
├── serviceAccountKey_members.json  # ← Firebase 会员系统服务账号密钥
└── app_server.py
```

**获取方式：**
1. 访问 [Firebase Console](https://console.firebase.google.com/project/eastern-market-members/settings/serviceaccounts/adminsdk)
2. 选择 "eastern-market-members" 项目
3. 点击 "生成新的私钥"
4. 下载并重命名为 `serviceAccountKey_members.json`

### 2. 依赖安装
```bash
pip install firebase-admin
```

## 📚 API 函数说明

### 1. `get_member_by_phone(phone: str) -> dict | None`

通过电话号码查询会员信息。

**参数：**
- `phone`: 电话号码（任意格式，自动标准化为 +1XXXXXXXXXX）

**返回：**
- 成功：会员数据字典（包含 uid, name, phone, tier, totalPoints 等）
- 失败：`None`

**示例：**
```python
from member_connector import get_member_by_phone

# 支持多种格式
member = get_member_by_phone("639-123-4567")
member = get_member_by_phone("6391234567")
member = get_member_by_phone("+16391234567")

if member:
    print(f"会员: {member['name']}")
    print(f"等级: {member['tier']}")
    print(f"积分: {member['totalPoints']}")
```

---

### 2. `add_points(member_id, points, order_id, amount, source="clover") -> bool`

为会员添加积分（原子操作）。

**参数：**
- `member_id`: 会员 UID
- `points`: 积分数量
- `order_id`: 订单 ID（Clover Order ID）
- `amount`: 订单金额
- `source`: 来源（默认 "clover"，可选 "web", "admin"）

**功能：**
- 原子更新 `totalPoints` 和 `lifetimePoints`
- 自动检查并升级会员等级：
  - 0-999 分 → Bronze
  - 1000-4999 分 → Silver（积分倍率 1.5x）
  - 5000+ 分 → Gold（积分倍率 2.0x）
- 记录积分交易历史

**返回：**
- 成功：`True`
- 失败：`False`

**示例：**
```python
from member_connector import add_points

# Clover 订单完成后添加积分
success = add_points(
    member_id="abc123xyz",
    points=50,
    order_id="CLOVER_ORDER_123",
    amount=50.00,
    source="clover"
)

if success:
    print("✅ 积分添加成功")
```

---

### 3. `get_member_points_history(member_id, limit=20) -> list`

获取会员积分历史记录。

**参数：**
- `member_id`: 会员 UID
- `limit`: 返回记录数量（默认 20）

**返回：**
- 积分交易记录列表（按时间倒序）

**示例：**
```python
from member_connector import get_member_points_history

history = get_member_points_history("abc123xyz", limit=10)

for tx in history:
    print(f"{tx['type']}: {tx['points']} 分 - {tx['description']}")
```

---

### 4. `adjust_points_manual(member_id, points, staff_note, admin_uid) -> bool`

手动调整会员积分（管理员操作）。

**参数：**
- `member_id`: 会员 UID
- `points`: 积分变动（正数增加，负数减少）
- `staff_note`: 操作备注
- `admin_uid`: 管理员 UID

**功能：**
- 支持增加或扣除积分
- 扣除时检查余额是否足够
- 记录管理员操作日志

**返回：**
- 成功：`True`
- 失败：`False`

**示例：**
```python
from member_connector import adjust_points_manual

# 补偿积分
success = adjust_points_manual(
    member_id="abc123xyz",
    points=100,
    staff_note="系统错误补偿",
    admin_uid="admin_uid_123"
)

# 扣除积分
success = adjust_points_manual(
    member_id="abc123xyz",
    points=-50,
    staff_note="订单取消退回",
    admin_uid="admin_uid_123"
)
```

---

### 5. `get_all_members(limit=100, search=None) -> list`

获取会员列表，支持搜索。

**参数：**
- `limit`: 返回记录数量（默认 100）
- `search`: 搜索关键词（姓名或手机号，可选）

**返回：**
- 会员列表（按积分倒序）

**示例：**
```python
from member_connector import get_all_members

# 获取积分最高的 50 位会员
top_members = get_all_members(limit=50)

# 搜索会员
results = get_all_members(search="张三")
results = get_all_members(search="639-123-4567")

for member in top_members:
    print(f"{member['name']} - {member['tier']} - {member['totalPoints']} 分")
```

---

## 🔗 集成到 StockWise

### 在 app_server.py 中集成

```python
from member_connector import (
    get_member_by_phone,
    add_points,
    get_member_points_history
)

# 示例：Clover 订单完成后添加积分
@app.post("/api/orders/complete")
async def complete_order(order_data: dict):
    phone = order_data.get("customer_phone")
    amount = order_data.get("total_amount")
    order_id = order_data.get("order_id")
    
    # 查询会员
    member = get_member_by_phone(phone)
    
    if member:
        # 计算积分（$1 = 1分）
        points = int(amount)
        
        # 添加积分
        success = add_points(
            member_id=member['uid'],
            points=points,
            order_id=order_id,
            amount=amount,
            source="clover"
        )
        
        if success:
            return {
                "success": True,
                "message": f"积分已添加：+{points} 分",
                "member": {
                    "name": member['name'],
                    "tier": member['tier']
                }
            }
    
    return {"success": False, "message": "非会员订单"}
```

### 新增 API 端点示例

```python
@app.get("/api/members/search")
async def search_member(phone: str):
    """通过电话号码查询会员"""
    member = get_member_by_phone(phone)
    if member:
        return {"success": True, "member": member}
    return {"success": False, "message": "会员不存在"}

@app.get("/api/members/{member_id}/points")
async def get_points_history(member_id: str, limit: int = 20):
    """获取会员积分历史"""
    history = get_member_points_history(member_id, limit)
    return {"success": True, "history": history}

@app.post("/api/members/{member_id}/adjust-points")
async def adjust_points(
    member_id: str,
    points: int,
    staff_note: str,
    admin_uid: str
):
    """手动调整积分（管理员）"""
    success = adjust_points_manual(member_id, points, staff_note, admin_uid)
    return {"success": success}
```

## 🔒 安全注意事项

1. **服务账号密钥保护**
   - 不要提交到 Git（已在 `.gitignore` 中）
   - 生产环境使用环境变量或密钥管理服务

2. **权限控制**
   - `adjust_points_manual` 需要验证管理员权限
   - API 端点需要添加身份验证

3. **错误处理**
   - 所有函数已包含完整的 try/except
   - 错误时打印详细日志并返回安全值

## 📊 数据结构

### Members Collection
```typescript
{
  uid: string,              // 文档 ID
  name: string,             // 会员姓名
  phone: string,            // +1XXXXXXXXXX
  email: string,
  totalPoints: number,      // 当前积分余额
  lifetimePoints: number,   // 累计获得积分
  tier: 'bronze' | 'silver' | 'gold',
  joinDate: string,         // YYYY-MM-DD
  language: 'en' | 'zh',
  isActive: boolean
}
```

### Points Transactions Collection
```typescript
{
  memberId: string,
  type: 'earn' | 'redeem' | 'adjust',
  points: number,           // 正数=增加，负数=减少
  orderId?: string,         // Clover Order ID
  amount?: number,          // 订单金额
  description: string,
  source: 'clover' | 'web' | 'manual',
  adminUid?: string,        // 管理员操作时
  staffNote?: string,       // 管理员备注
  createdAt: Timestamp
}
```

## 🧪 测试

运行模块测试：
```bash
cd d:\stockwise_final
python member_connector.py
```

## 📞 支持

- **Firebase 项目**: eastern-market-members
- **项目 ID**: eastern-market-members
- **控制台**: https://console.firebase.google.com/project/eastern-market-members
