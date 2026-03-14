#!/usr/bin/env python3
"""
清理所有 name 为空的商品记录
"""

import os
from firebase_config import get_firestore_client

def cleanup_empty_products():
    """清理所有 name 为空的商品记录"""
    print("🔍 开始清理空名称商品记录...")
    
    try:
        # 获取 Firestore 客户端
        db = get_firestore_client()
        products_ref = db.collection('products')
        
        # 获取所有空名称的记录
        print("📋 查询空名称商品记录...")
        empty_products = products_ref.where('name', '==', '').stream()
        
        # 统计和批量删除
        batch = db.batch()
        count = 0
        deleted_count = 0
        
        for doc in empty_products:
            batch.delete(doc.reference)
            count += 1
            deleted_count += 1
            
            # Firestore 批量操作上限 500
            if count % 500 == 0:
                print(f"🔄 提交批次 {count//500}，已删除 {deleted_count} 条记录...")
                batch.commit()
                batch = db.batch()
        
        # 提交剩余的记录
        if count % 500 != 0:
            print(f"🔄 提交最后批次，已删除 {deleted_count} 条记录...")
            batch.commit()
        
        print(f"✅ 清理完成！共删除 {deleted_count} 条空记录")
        
        # 验证清理结果
        remaining_empty = list(products_ref.where('name', '==', '').stream())
        if remaining_empty:
            print(f"⚠️  警告：仍有 {len(remaining_empty)} 条空记录")
        else:
            print("🎉 验证通过：所有空记录已清理完毕")
            
        return deleted_count
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return 0

def show_product_stats():
    """显示商品统计信息"""
    try:
        db = get_firestore_client()
        products_ref = db.collection('products')
        
        # 总商品数
        total_products = len(list(products_ref.stream()))
        
        # 空名称商品数
        empty_name_products = len(list(products_ref.where('name', '==', '').stream()))
        
        # 有名称商品数
        named_products = total_products - empty_name_products
        
        print(f"📊 商品统计:")
        print(f"   总商品数: {total_products}")
        print(f"   空名称商品: {empty_name_products}")
        print(f"   有名称商品: {named_products}")
        
        return {
            'total': total_products,
            'empty_name': empty_name_products,
            'named': named_products
        }
        
    except Exception as e:
        print(f"❌ 统计失败: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("🧹 商品记录清理工具")
    print("=" * 50)
    
    # 显示清理前统计
    print("\n📈 清理前统计:")
    show_product_stats()
    
    # 确认清理
    print("\n⚠️  即将删除所有 name 为空的商品记录")
    print("请确认是否继续 (y/N): ", end="")
    
    try:
        confirm = input().lower().strip()
        if confirm in ['y', 'yes', '是']:
            print("\n🚀 开始清理...")
            deleted = cleanup_empty_products()
            
            print("\n📈 清理后统计:")
            show_product_stats()
            
            print(f"\n🎯 清理总结: 成功删除 {deleted} 条空记录")
        else:
            print("\n❌ 用户取消清理操作")
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断清理操作")
