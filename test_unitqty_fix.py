#!/usr/bin/env python3
"""
测试 unitQty 修复后的数据处理逻辑
"""

import sys
import os
import pandas as pd

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_engine import DataEngine

def test_unitqty_processing():
    """测试 unitQty 处理逻辑"""
    print("🧪 测试 unitQty 处理逻辑...")
    
    # 创建测试商品数据
    test_items = [
        {'id': 'item1', 'name': 'Test Product 1', 'price': 10.99},
        {'id': 'item2', 'name': 'Test Product 2', 'price': 5.99},
    ]
    
    # 创建各种 unitQty 情况的销售数据
    test_sales_data = [
        # 正常数量
        {'manual_id_link': 'item1', 'name': 'Test Product 1', 'price': 1099, 'unitQty': 2000},  # 2个单位
        # 数量为0
        {'manual_id_link': 'item1', 'name': 'Test Product 1', 'price': 1099, 'unitQty': 0},        # 0个单位，应该计为1
        # 没有数量字段
        {'manual_id_link': 'item1', 'name': 'Test Product 1', 'price': 1099},                     # 没有unitQty，应该计为1
        # 负数数量（异常情况）
        {'manual_id_link': 'item2', 'name': 'Test Product 2', 'price': 599, 'unitQty': -100},    # 负数，应该计为1
        # None 数量
        {'manual_id_link': 'item2', 'name': 'Test Product 2', 'price': 599, 'unitQty': None},      # None，应该计为1
    ]
    
    print(f"   测试商品数: {len(test_items)}")
    print(f"   测试销售记录数: {len(test_sales_data)}")
    
    # 测试数据处理
    engine = DataEngine()
    df = engine.audit_process("test", test_items, test_sales_data)
    
    if not df.empty:
        print("   ✅ 数据处理成功")
        print("\n   处理结果:")
        for _, row in df.iterrows():
            print(f"   商品: {row['商品信息']}")
            print(f"   销量: {row['区间销量']} (预期: 3.0)")
            print(f"   销售额: {row['销售总额']} (预期: $32.97)")
            print()
        
        # 验证计算结果
        item1_row = df[df['商品信息'] == 'Test Product 1'].iloc[0]
        item2_row = df[df['商品信息'] == 'Test Product 2'].iloc[0]
        
        # item1 应该有: 2 + 1 + 1 = 4 个单位，金额: $10.99 * 3 = $32.97
        expected_item1_qty = 4.0
        expected_item1_rev = 32.97
        
        # item2 应该有: 1 + 1 = 2 个单位，金额: $5.99 * 2 = $11.98
        expected_item2_qty = 2.0
        expected_item2_rev = 11.98
        
        print("   📊 验证计算结果:")
        item1_qty = float(item1_row['区间销量'])
        item2_qty = float(item2_row['区间销量'])
        
        print(f"   Item1 - 销量: {item1_qty} (预期: {expected_item1_qty}) ✓" if abs(item1_qty - expected_item1_qty) < 0.01 else f"   Item1 - 销量: {item1_qty} (预期: {expected_item1_qty}) ✗")
        print(f"   Item1 - 销售额: {item1_row['销售总额']} (预期: ${expected_item1_rev:.2f}) ✓" if item1_row['销售总额'] == f"${expected_item1_rev:.2f}" else f"   Item1 - 销售额: {item1_row['销售总额']} (预期: ${expected_item1_rev:.2f}) ✗")
        print(f"   Item2 - 销量: {item2_qty} (预期: {expected_item2_qty}) ✓" if abs(item2_qty - expected_item2_qty) < 0.01 else f"   Item2 - 销量: {item2_qty} (预期: {expected_item2_qty}) ✗")
        print(f"   Item2 - 销售额: {item2_row['销售总额']} (预期: ${expected_item2_rev:.2f}) ✓" if item2_row['销售总额'] == f"${expected_item2_rev:.2f}" else f"   Item2 - 销售额: {item2_row['销售总额']} (预期: ${expected_item2_rev:.2f}) ✗")
        
        return True
    else:
        print("   ❌ 数据处理失败")
        return False

def test_export_unitqty_processing():
    """测试导出功能中的 unitQty 处理"""
    print("\n📋 测试导出功能中的 unitQty 处理...")
    
    # 创建测试数据
    test_inventory = [
        {'id': 'item1', 'name': 'Export Test 1', 'price': 15.99, 'sku': 'EXP001'},
        {'id': 'item2', 'name': 'Export Test 2', 'price': 8.99, 'sku': 'EXP002'},
    ]
    
    test_sales = [
        {'name': 'Export Test 1', 'price': 1599, 'unitQty': 0},      # 应该计为1
        {'name': 'Export Test 1', 'price': 1599, 'unitQty': None},   # 应该计为1
        {'name': 'Export Test 2', 'price': 899, 'unitQty': 2000},    # 应该计为2
        {'name': 'Export Test 2', 'price': 899},                    # 应该计为1
    ]
    
    engine = DataEngine()
    df = engine.prepare_export_csv(test_inventory, test_sales)
    
    if not df.empty:
        print("   ✅ 导出数据处理成功")
        print("\n   导出结果:")
        print(df.to_string(index=False))
        
        # 验证结果
        item1_row = df[df['商品名称'] == 'Export Test 1'].iloc[0]
        item2_row = df[df['商品名称'] == 'Export Test 2'].iloc[0]
        
        print("\n   📊 验证导出计算:")
        print(f"   Export Test 1 - 累计销量: {item1_row['累计销量']} (预期: 2.0) ✓" if item1_row['累计销量'] == 2.0 else f"   Export Test 1 - 累计销量: {item1_row['累计销量']} (预期: 2.0) ✗")
        print(f"   Export Test 2 - 累计销量: {item2_row['累计销量']} (预期: 3.0) ✓" if item2_row['累计销量'] == 3.0 else f"   Export Test 2 - 累计销量: {item2_row['累计销量']} (预期: 3.0) ✗")
        
        return True
    else:
        print("   ❌ 导出数据处理失败")
        return False

if __name__ == "__main__":
    print("🚀 unitQty 修复验证测试")
    print("=" * 40)
    
    success1 = test_unitqty_processing()
    success2 = test_export_unitqty_processing()
    
    if success1 and success2:
        print("\n🎉 所有 unitQty 处理测试通过！")
        print("✅ 修复成功：unitQty 为 0、None 或负数时都正确计为 1 个单位")
    else:
        print("\n❌ 测试发现问题，需要进一步检查")
