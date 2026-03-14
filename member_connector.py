"""
会员系统集成模块
连接 StockWise 与 Firebase 会员系统
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Optional, List, Dict
import re


try:
    cred_members = credentials.Certificate("serviceAccountKey_members.json")
    members_app = firebase_admin.initialize_app(
        cred_members,
        name="members_app"
    )
    db_members = firestore.client(app=members_app)
    print("✅ Firebase 会员系统初始化成功")
except Exception as e:
    print(f"⚠️ Firebase 会员系统初始化失败: {e}")
    db_members = None


def normalize_phone(phone: str) -> str:
    """
    标准化电话号码格式为 +1XXXXXXXXXX
    """
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    else:
        return f"+1{digits[-10:]}" if len(digits) >= 10 else phone


def get_member_by_phone(phone: str) -> Optional[Dict]:
    """
    通过电话号码查询会员
    
    Args:
        phone: 电话号码（任意格式）
        
    Returns:
        会员数据字典，不存在返回 None
    """
    if not db_members:
        print("❌ Firebase 会员系统未初始化")
        return None
    
    try:
        normalized_phone = normalize_phone(phone)
        
        members_ref = db_members.collection('members')
        query = members_ref.where('phone', '==', normalized_phone).limit(1)
        results = query.get()
        
        if not results:
            print(f"ℹ️ 未找到电话号码为 {normalized_phone} 的会员")
            return None
        
        member_doc = results[0]
        member_data = member_doc.to_dict()
        member_data['uid'] = member_doc.id
        
        print(f"✅ 找到会员: {member_data.get('name')} ({normalized_phone})")
        return member_data
        
    except Exception as e:
        print(f"❌ 查询会员失败 (phone={phone}): {e}")
        return None


def calculate_tier(lifetime_points: int) -> str:
    """
    根据累计积分计算会员等级
    
    Args:
        lifetime_points: 累计积分
        
    Returns:
        会员等级 ('bronze', 'silver', 'gold')
    """
    if lifetime_points >= 5000:
        return 'gold'
    elif lifetime_points >= 1000:
        return 'silver'
    else:
        return 'bronze'


def add_points(
    member_id: str,
    points: int,
    order_id: str,
    amount: float,
    source: str = "clover"
) -> bool:
    """
    为会员添加积分（原子操作）
    
    Args:
        member_id: 会员 UID
        points: 积分数量
        order_id: 订单 ID
        amount: 订单金额
        source: 来源 (clover/web/admin)
        
    Returns:
        True 成功，False 失败
    """
    if not db_members:
        print("❌ Firebase 会员系统未初始化")
        return False
    
    try:
        batch = db_members.batch()
        
        member_ref = db_members.collection('members').document(member_id)
        member_doc = member_ref.get()
        
        if not member_doc.exists:
            print(f"❌ 会员不存在: {member_id}")
            return False
        
        member_data = member_doc.to_dict()
        current_lifetime = member_data.get('lifetimePoints', 0)
        new_lifetime = current_lifetime + points
        new_tier = calculate_tier(new_lifetime)
        
        transaction_ref = db_members.collection('points_transactions').document()
        batch.set(transaction_ref, {
            'memberId': member_id,
            'type': 'earn',
            'points': points,
            'orderId': order_id,
            'amount': amount,
            'description': f'购物消费 ${amount:.2f} 获得积分',
            'source': source,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        batch.update(member_ref, {
            'totalPoints': firestore.Increment(points),
            'lifetimePoints': firestore.Increment(points),
            'tier': new_tier,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        batch.commit()
        
        tier_changed = new_tier != member_data.get('tier')
        tier_msg = f" → 等级升级至 {new_tier.upper()}" if tier_changed else ""
        print(f"✅ 积分添加成功: {member_data.get('name')} +{points} 积分{tier_msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ 添加积分失败 (member_id={member_id}, points={points}): {e}")
        return False


def get_member_points_history(member_id: str, limit: int = 20) -> List[Dict]:
    """
    获取会员积分历史记录
    
    Args:
        member_id: 会员 UID
        limit: 返回记录数量限制
        
    Returns:
        积分交易记录列表
    """
    if not db_members:
        print("❌ Firebase 会员系统未初始化")
        return []
    
    try:
        transactions_ref = db_members.collection('points_transactions')
        query = transactions_ref.where('memberId', '==', member_id) \
                                .order_by('createdAt', direction=firestore.Query.DESCENDING) \
                                .limit(limit)
        
        results = query.get()
        
        history = []
        for doc in results:
            data = doc.to_dict()
            data['id'] = doc.id
            
            if 'createdAt' in data and data['createdAt']:
                data['createdAt'] = data['createdAt'].isoformat()
            
            history.append(data)
        
        print(f"✅ 获取积分历史成功: {len(history)} 条记录")
        return history
        
    except Exception as e:
        print(f"❌ 获取积分历史失败 (member_id={member_id}): {e}")
        return []


def adjust_points_manual(
    member_id: str,
    points: int,
    staff_note: str,
    admin_uid: str
) -> bool:
    """
    手动调整会员积分（管理员操作）
    
    Args:
        member_id: 会员 UID
        points: 积分变动（正数增加，负数减少）
        staff_note: 操作备注
        admin_uid: 管理员 UID
        
    Returns:
        True 成功，False 失败
    """
    if not db_members:
        print("❌ Firebase 会员系统未初始化")
        return False
    
    try:
        batch = db_members.batch()
        
        member_ref = db_members.collection('members').document(member_id)
        member_doc = member_ref.get()
        
        if not member_doc.exists:
            print(f"❌ 会员不存在: {member_id}")
            return False
        
        member_data = member_doc.to_dict()
        current_total = member_data.get('totalPoints', 0)
        current_lifetime = member_data.get('lifetimePoints', 0)
        
        if points < 0 and current_total + points < 0:
            print(f"❌ 积分不足: 当前 {current_total}，尝试扣除 {abs(points)}")
            return False
        
        new_lifetime = max(0, current_lifetime + points) if points > 0 else current_lifetime
        new_tier = calculate_tier(new_lifetime)
        
        transaction_ref = db_members.collection('points_transactions').document()
        batch.set(transaction_ref, {
            'memberId': member_id,
            'type': 'adjust',
            'points': points,
            'description': staff_note,
            'source': 'manual',
            'adminUid': admin_uid,
            'staffNote': staff_note,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        update_data = {
            'totalPoints': firestore.Increment(points),
            'tier': new_tier,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }
        
        if points > 0:
            update_data['lifetimePoints'] = firestore.Increment(points)
        
        batch.update(member_ref, update_data)
        
        batch.commit()
        
        action = "增加" if points > 0 else "扣除"
        print(f"✅ 手动调整成功: {member_data.get('name')} {action} {abs(points)} 积分")
        print(f"   备注: {staff_note}")
        
        return True
        
    except Exception as e:
        print(f"❌ 手动调整积分失败 (member_id={member_id}, points={points}): {e}")
        return False


def get_all_members(limit: int = 100, search: Optional[str] = None) -> List[Dict]:
    """
    获取所有会员列表
    
    Args:
        limit: 返回记录数量限制
        search: 搜索关键词（姓名或手机号）
        
    Returns:
        会员列表
    """
    if not db_members:
        print("❌ Firebase 会员系统未初始化")
        return []
    
    try:
        members_ref = db_members.collection('members')
        
        if search:
            search = search.strip()
            if search.startswith('+') or search.isdigit():
                normalized_search = normalize_phone(search)
                query = members_ref.where('phone', '==', normalized_search).limit(limit)
            else:
                query = members_ref.where('name', '>=', search) \
                                  .where('name', '<=', search + '\uf8ff') \
                                  .limit(limit)
        else:
            query = members_ref.order_by('totalPoints', direction=firestore.Query.DESCENDING) \
                              .limit(limit)
        
        results = query.get()
        
        members = []
        for doc in results:
            data = doc.to_dict()
            member_info = {
                'uid': doc.id,
                'name': data.get('name', ''),
                'phone': data.get('phone', ''),
                'tier': data.get('tier', 'bronze'),
                'totalPoints': data.get('totalPoints', 0),
                'joinDate': data.get('joinDate', '')
            }
            members.append(member_info)
        
        search_msg = f" (搜索: {search})" if search else ""
        print(f"✅ 获取会员列表成功: {len(members)} 条记录{search_msg}")
        return members
        
    except Exception as e:
        print(f"❌ 获取会员列表失败: {e}")
        return []


if __name__ == "__main__":
    print("\n=== 会员系统集成模块测试 ===\n")
    
    test_phone = "+16391234567"
    member = get_member_by_phone(test_phone)
    
    if member:
        print(f"\n会员信息:")
        print(f"  姓名: {member.get('name')}")
        print(f"  等级: {member.get('tier')}")
        print(f"  积分: {member.get('totalPoints')}")
        
        history = get_member_points_history(member['uid'], limit=5)
        print(f"\n最近 {len(history)} 条积分记录:")
        for tx in history:
            print(f"  {tx.get('type')}: {tx.get('points')} 分 - {tx.get('description')}")
    
    all_members = get_all_members(limit=10)
    print(f"\n会员总数（前10）: {len(all_members)}")
    for m in all_members[:3]:
        print(f"  {m['name']} - {m['tier']} - {m['totalPoints']} 分")
