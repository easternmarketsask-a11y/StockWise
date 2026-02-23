import pandas as pd

class DataEngine:
    @staticmethod
    def audit_process(query, inventory, raw_sales):
        """精准审计：支持 ID 链接和名称双重校验"""
        q = str(query).strip().lower()
        matched_items = [
            i for i in inventory 
            if q in str(i.get('name') or "").lower() or \
               q in str(i.get('sku') or "").lower() or \
               q in str(i.get('code') or "").lower() or \
               q in str(i.get('alt_code') or "").lower()
        ]
        
        if not matched_items: return pd.DataFrame()

        # 统计容器
        sales_stats = {m['id']: {"qty": 0, "rev": 0} for m in matched_items}
        name_map = {m['name'].lower(): m['id'] for m in matched_items}
        
        for s in raw_sales:
            # 1. 优先尝试手动贴上的 ID 链接
            target_id = s.get('manual_id_link')
            
            # 2. 如果没有手动链接（如全店导出模式），尝试名称比对
            if not target_id:
                s_name = str(s.get("name") or "").lower()
                target_id = name_map.get(s_name)
            
            if target_id and target_id in sales_stats:
                u_qty = s.get("unitQty")
                val = (u_qty / 1000) if u_qty is not None else 1
                sales_stats[target_id]["qty"] += val
                sales_stats[target_id]["rev"] += (s.get("price", 0) / 100)

        res = []
        for m in matched_items:
            st_data = sales_stats[m['id']]
            res.append({
                "商品信息": m['name'], "售价": f"${m['price']:.2f}", 
                "区间销量": round(st_data['qty'], 2), "销售总额": f"${st_data['rev']:.2f}", 
                "标识符": f"{m.get('sku') or m.get('code') or '-'}"
            })
        return pd.DataFrame(res)

    @staticmethod
    def prepare_export_csv(inventory, raw_sales):
        """报表导出处理"""
        if not raw_sales: return pd.DataFrame()
        inv_lookup = {item['id']: item for item in inventory}
        summary = {}
        for s in raw_sales:
            name = str(s.get("name") or "Unknown").strip()
            item_id = s.get("item", {}).get("id")
            key = item_id if item_id else f"T_{name}"
            if key not in summary:
                ref = inv_lookup.get(item_id, {})
                summary[key] = {"商品名称": name, "SKU": ref.get("sku", "-"), "Product Code": ref.get("code", "-"), "累计销量": 0.0, "累计金额": 0.0}
            u_qty = s.get("unitQty")
            val = (u_qty / 1000) if u_qty is not None else 1
            summary[key]["累计销量"] += val
            summary[key]["累计金额"] += (s.get("price", 0) / 100)
            
        df = pd.DataFrame(list(summary.values())).sort_values(by="累计销量", ascending=False)
        df["累计金额"] = df["累计金额"].map(lambda x: f"${x:,.2f}")
        return df