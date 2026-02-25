import requests
import streamlit as st
import os
from dotenv import load_dotenv

class CloverAPIHandler:
    def __init__(self):
        # 尝试加载 .env 文件
        load_dotenv()
        
        # 支持多种环境变量名称格式
        self.api_key = str(os.environ.get("CLOVER_API_KEY", "")).strip()
        self.merchant_id = str(os.environ.get("MERCHANT_ID", "")).strip() or str(os.environ.get("CLOVER_MERCHANT_ID", "")).strip()
        
        # 显示配置状态（仅用于调试）
        if not self.api_key or not self.merchant_id:
            st.error("⚠️ API 配置缺失：请设置环境变量")
            st.info("📝 环境变量设置：")
            st.info("• CLOVER_API_KEY")
            st.info("• MERCHANT_ID 或 CLOVER_MERCHANT_ID")
        
        self.base_url = f"https://api.clover.com/v3/merchants/{self.merchant_id}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    @st.cache_data(ttl=1800)
    def fetch_full_inventory(_self):
        items = []
        limit, offset = 1000, 0
        try:
            while True:
                url = f"{_self.base_url}/items"
                res = requests.get(url, headers=_self.headers, params={"limit": limit, "offset": offset}, timeout=15)
                
                # 检查响应状态
                if res.status_code != 200:
                    st.error(f"❌ API 请求失败: HTTP {res.status_code}")
                    st.error(f"📝 响应内容: {res.text[:200]}...")
                    return []
                
                data = res.json().get("elements", [])
                for e in data:
                    items.append({
                        "id": e.get("id"),
                        "name": str(e.get("name") or ""),
                        "sku": str(e.get("sku") or ""),
                        "code": str(e.get("code") or ""),
                        "alt_code": str(e.get("alternateCode") or ""),
                        "price": e.get("price", 0) / 100
                    })
                if len(data) < limit: break
                offset += limit
            return items
        except requests.exceptions.RequestException as e:
            st.error(f"🌐 网络请求错误: {str(e)}")
            st.error("💡 可能原因: 网络连接问题、API 服务器无响应或防火墙阻止")
            return []
        except Exception as e:
            st.error(f"❌ 未知错误: {str(e)}")
            st.error(f"🔍 调试信息: API Key 长度={len(self.api_key)}, Merchant ID={self.merchant_id}")
            return []

    def fetch_targeted_sales(self, item_ids, start_ts, end_ts):
        """100% 还原 v1.3.1 逻辑：逐个 ID 精准打击，支持跨年"""
        all_data = []
        for item_id in item_ids:
            offset = 0
            while True:
                # 核心修复：使用元组列表确保过滤器语法在所有服务器上一致
                params = [
                    ('filter', f'item.id={item_id}'),
                    ('filter', f'createdTime>{start_ts}'),
                    ('filter', f'createdTime<{end_ts}'),
                    ('limit', '1000'),
                    ('offset', str(offset))
                ]
                try:
                    res = requests.get(f"{self.base_url}/line_items", headers=self.headers, params=params, timeout=20)
                    data = res.json().get("elements", [])
                    # 关键加固：手动建立 ID 关联，不依赖 API 的 expand
                    for record in data:
                        record['manual_id_link'] = item_id
                    all_data.extend(data)
                    if len(data) < 1000: break
                    offset += 1000
                except: break
        return all_data

    def fetch_full_period_sales(self, start_ts, end_ts):
        """导出功能专用"""
        all_data = []
        limit, offset = 1000, 0
        status_p = st.empty()
        try:
            while True:
                params = [
                    ('filter', f'createdTime>{start_ts}'),
                    ('filter', f'createdTime<{end_ts}'),
                    ('expand', 'item'),
                    ('limit', '1000'),
                    ('offset', str(offset))
                ]
                res = requests.get(f"{self.base_url}/line_items", headers=self.headers, params=params, timeout=30)
                
                # 检查响应状态
                if res.status_code != 200:
                    st.error(f"❌ API 请求失败: HTTP {res.status_code}")
                    st.error(f"📝 响应内容: {res.text[:200]}...")
                    return None  # 返回None表示API失败
                
                data = res.json().get("elements", [])
                if not data: break
                all_data.extend(data)
                status_p.caption(f"已同步 {len(all_data)} 条销售流水...")
                if len(data) < limit: break
                offset += limit
            status_p.empty()
            return all_data
        except requests.exceptions.RequestException as e:
            st.error(f"🌐 网络请求错误: {str(e)}")
            st.error("💡 可能原因: 网络连接问题、API 服务器无响应或防火墙阻止")
            return None  # 返回None表示网络错误
        except Exception as e:
            st.error(f"❌ 未知错误: {str(e)}")
            return None  # 返回None表示其他错误