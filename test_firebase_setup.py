#!/usr/bin/env python3
"""
测试Firebase设置
"""

import os
from firebase_config import get_firestore_client, get_storage_bucket

def test_firebase_connection():
    print("🔍 测试Firebase连接...")
    
    try:
        # 测试Firestore连接
        print("📊 测试Firestore连接...")
        db = get_firestore_client()
        
        # 测试基本操作
        test_doc = {
            "name": "测试商品",
            "price": 9.99,
            "category": "测试分类",
            "created_at": "2026-03-11T10:00:00"
        }
        
        # 添加测试文档
        doc_ref = db.collection("products").add(test_doc)
        doc_id = doc_ref[1].id
        print(f"✅ Firestore写入成功: {doc_id}")
        
        # 读取测试文档
        doc = db.collection("products").document(doc_id).get()
        if doc.exists:
            print(f"✅ Firestore读取成功: {doc.to_dict()}")
        
        # 删除测试文档
        db.collection("products").document(doc_id).delete()
        print("✅ Firestore删除成功")
        
    except Exception as e:
        print(f"❌ Firestore连接失败: {e}")
        return False
    
    try:
        # 测试Cloud Storage连接
        print("📁 测试Cloud Storage连接...")
        bucket = get_storage_bucket()
        
        # 测试文件列表
        blobs = bucket.list_blobs(max_results=1)
        print("✅ Cloud Storage连接成功")
        
        # 获取bucket名称
        print(f"📦 Storage Bucket: {bucket.name}")
        
    except Exception as e:
        print(f"❌ Cloud Storage连接失败: {e}")
        return False
    
    print("🎉 Firebase设置完成！")
    return True

if __name__ == "__main__":
    test_firebase_connection()
