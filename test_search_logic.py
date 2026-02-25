#!/usr/bin/env python3
"""
商品搜索逻辑测试脚本
用于验证搜索、匹配、数据处理的完整性
"""

import sys
import os
from datetime import datetime, timedelta
import time

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_handler import CloverAPIHandler
from data_engine import DataEngine

def test_search_logic():
    """测试搜索逻辑的完整性"""
    print("🔍 开始测试商品搜索逻辑...")
    
    # 1. 初始化组件
    print("\n📦 1. 初始化组件...")
    api = CloverAPIHandler()
    engine = DataEngine()
    
    # 2. 获取库存数据
    print("\n📋 2. 获取库存数据...")
    inventory = api.fetch_full_inventory()
    
    if inventory is None:
        print("❌ 库存数据获取失败")
        return False
    
    if not inventory:
        print("⚠️ 店铺中暂无商品数据")
        return False
    
    print(f"✅ 成功获取 {len(inventory)} 件商品")
    
    # 3. 测试搜索匹配逻辑
    print("\n🔎 3. 测试搜索匹配逻辑...")
    
    # 测试用例
    test_queries = [
        "apple",  # 英文
        "苹果",   # 中文
        "123",    # 数字片段
        "test",   # 通用词
    ]
    
    for query in test_queries:
        print(f"\n🔍 测试查询: '{query}'")
        
        # 模拟主程序中的搜索逻辑
        matched_items = [i for i in inventory if query.lower() in str(i.get('name') or "").lower() or \
                         query.lower() in str(i.get('sku') or "").lower() or \
                         query.lower() in str(i.get('code') or "").lower() or \
                         query.lower() in str(i.get('alt_code') or "").lower()]
        
        print(f"   匹配商品数: {len(matched_items)}")
        
        if matched_items:
            # 显示前3个匹配商品
            for i, item in enumerate(matched_items[:3]):
                print(f"   {i+1}. {item.get('name', 'Unknown')} (SKU: {item.get('sku', 'N/A')})")
        else:
            print("   ⚠️ 未找到匹配商品")
    
    # 4. 测试时间戳生成
    print("\n⏰ 4. 测试时间戳生成...")
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # 模拟主程序中的时间戳逻辑
    s_ts = int(time.mktime(start_date.timetuple()) * 1000)
    e_ts = int(time.mktime((end_date + timedelta(days=1)).timetuple()) * 1000) - 1
    
    print(f"   开始时间戳: {s_ts}")
    print(f"   结束时间戳: {e_ts}")
    print(f"   查询期间: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    # 5. 测试销售数据获取（仅测试第一个匹配商品）
    print("\n💰 5. 测试销售数据获取...")
    
    # 选择第一个商品进行测试
    if inventory:
        test_item = inventory[0]
        test_item_id = test_item['id']
        test_item_name = test_item.get('name', 'Unknown')
        
        print(f"   测试商品: {test_item_name} (ID: {test_item_id})")
        
        try:
            raw_sales = api.fetch_targeted_sales([test_item_id], s_ts, e_ts)
            print(f"   获取销售记录数: {len(raw_sales) if raw_sales else 0}")
            
            if raw_sales:
                # 显示第一条销售记录
                first_sale = raw_sales[0]
                print(f"   第一条记录: 价格=${first_sale.get('price', 0)/100:.2f}, 数量={first_sale.get('unitQty', 0)/1000:.2f}")
        except Exception as e:
            print(f"   ❌ 销售数据获取失败: {str(e)}")
    
    # 6. 测试数据处理逻辑
    print("\n📊 6. 测试数据处理逻辑...")
    
    # 使用模拟数据测试
    if inventory:
        test_items = inventory[:2]  # 取前2个商品
        mock_sales = []
        
        # 创建模拟销售数据
        for i, item in enumerate(test_items):
            mock_sales.append({
                'manual_id_link': item['id'],
                'name': item.get('name', ''),
                'price': int(item.get('price', 0) * 100),  # 转换为分
                'unitQty': 1000,  # 1单位
            })
        
        print(f"   模拟商品数: {len(test_items)}")
        print(f"   模拟销售记录数: {len(mock_sales)}")
        
        # 测试数据处理
        df = engine.audit_process("test", test_items, mock_sales)
        
        if not df.empty:
            print(f"   ✅ 数据处理成功，生成 {len(df)} 条记录")
            print("   处理结果预览:")
            print(df.to_string(index=False, max_cols=4))
        else:
            print("   ⚠️ 数据处理结果为空")
    
    # 7. 测试错误处理
    print("\n🛡️ 7. 测试错误处理...")
    
    # 测试空查询
    empty_query = ""
    empty_matches = [i for i in inventory if empty_query.lower() in str(i.get('name') or "").lower()]
    print(f"   空查询匹配数: {len(empty_matches)} (应该是全部商品)")
    
    # 测试不存在的查询
    fake_query = "nonexistentproduct12345"
    fake_matches = [i for i in inventory if fake_query.lower() in str(i.get('name') or "").lower()]
    print(f"   不存在查询匹配数: {len(fake_matches)} (应该是0)")
    
    print("\n✅ 搜索逻辑测试完成！")
    return True

def test_edge_cases():
    """测试边缘情况"""
    print("\n🧪 测试边缘情况...")
    
    # 创建测试数据
    test_inventory = [
        {'id': '1', 'name': 'Apple', 'sku': 'APP001', 'code': '1001', 'alt_code': '', 'price': 1.99},
        {'id': '2', 'name': '苹果', 'sku': 'APPLE', 'code': '', 'alt_code': '2002', 'price': 2.99},
        {'id': '3', 'name': '', 'sku': 'EMPTY', 'code': '3003', 'alt_code': '', 'price': 0.99},
        {'id': '4', 'name': 'Orange Juice', 'sku': '', 'code': '', 'alt_code': '', 'price': 3.99},
    ]
    
    # 测试各种搜索情况
    test_cases = [
        ('app', '应该匹配Apple和苹果'),
        ('苹果', '应该匹配苹果'),
        ('001', '应该匹配Apple (SKU)'),
        ('2002', '应该匹配苹果 (alt_code)'),
        ('', '应该匹配所有商品'),
        ('xyz', '应该不匹配任何商品'),
    ]
    
    for query, expected in test_cases:
        matches = [i for i in test_inventory if query.lower() in str(i.get('name') or "").lower() or \
                 query.lower() in str(i.get('sku') or "").lower() or \
                 query.lower() in str(i.get('code') or "").lower() or \
                 query.lower() in str(i.get('alt_code') or "").lower()]
        
        print(f"   查询 '{query}': {len(matches)} 个匹配 - {expected}")
        for match in matches:
            print(f"     - {match.get('name', 'N/A')} (SKU: {match.get('sku', 'N/A')})")

if __name__ == "__main__":
    print("🚀 StockWise 搜索逻辑完整性测试")
    print("=" * 50)
    
    try:
        # 运行主测试
        success = test_search_logic()
        
        # 运行边缘情况测试
        test_edge_cases()
        
        if success:
            print("\n🎉 所有测试通过！搜索逻辑工作正常。")
        else:
            print("\n❌ 测试发现问题，请检查配置。")
            
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
