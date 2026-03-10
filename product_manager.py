"""
Product Manager Module - Backend product editing and storage
Provides persistent storage for product information with edit capabilities
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ProductManager:
    """Manages product data storage and editing"""
    
    def __init__(self, storage_path: str = "data/products.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.products: Dict[str, Dict] = {}
        self._load_products()
    
    def _load_products(self):
        """Load products from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.products = json.load(f)
                logger.info(f"Loaded {len(self.products)} products from storage")
            except Exception as e:
                logger.error(f"Failed to load products: {e}")
                self.products = {}
        else:
            self.products = {}
    
    def _save_products(self):
        """Save products to storage"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.products)} products to storage")
            return True
        except Exception as e:
            logger.error(f"Failed to save products: {e}")
            return False
    
    def get_product_key(self, product_id: str = None, name: str = None, sku: str = None, code: str = None) -> str:
        """Generate unique product key"""
        if product_id:
            return f"id_{product_id}"
        return f"key_{name}_{sku}_{code}"
    
    def get_product(self, product_id: str = None, name: str = None, sku: str = None, code: str = None) -> Optional[Dict]:
        """Get product by ID or composite key"""
        key = self.get_product_key(product_id, name, sku, code)
        return self.products.get(key)
    
    def save_product(self, product_data: Dict) -> Dict:
        """Save or update product information"""
        product_id = product_data.get("id")
        name = product_data.get("name", "")
        sku = product_data.get("sku", "")
        code = product_data.get("code", "")
        
        key = self.get_product_key(product_id, name, sku, code)
        
        # Merge with existing data if present
        existing = self.products.get(key, {})
        
        # Update timestamp
        now = datetime.now().isoformat()
        if not existing:
            product_data["created_at"] = now
        product_data["updated_at"] = now
        
        # Merge data
        existing.update(product_data)
        self.products[key] = existing
        
        # Save to disk
        self._save_products()
        
        return existing
    
    def update_product_field(self, product_key: str, field: str, value) -> Optional[Dict]:
        """Update a specific field of a product"""
        if product_key not in self.products:
            return None
        
        self.products[product_key][field] = value
        self.products[product_key]["updated_at"] = datetime.now().isoformat()
        
        self._save_products()
        return self.products[product_key]
    
    def delete_product(self, product_key: str) -> bool:
        """Delete a product"""
        if product_key in self.products:
            del self.products[product_key]
            self._save_products()
            return True
        return False
    
    def get_all_products(self, filters: Dict = None) -> List[Dict]:
        """Get all products with optional filters"""
        products = list(self.products.values())
        
        if not filters:
            return products
        
        # Apply filters
        filtered = products
        
        if "category" in filters:
            filtered = [p for p in filtered if p.get("category") == filters["category"]]
        
        if "has_description" in filters:
            if filters["has_description"]:
                filtered = [p for p in filtered if p.get("description")]
            else:
                filtered = [p for p in filtered if not p.get("description")]
        
        if "search" in filters:
            search_term = filters["search"].lower()
            filtered = [p for p in filtered 
                       if search_term in p.get("name", "").lower() 
                       or search_term in p.get("sku", "").lower()
                       or search_term in p.get("code", "").lower()]
        
        return filtered
    
    def bulk_update(self, updates: List[Dict]) -> Dict:
        """Bulk update multiple products"""
        success_count = 0
        failed_count = 0
        errors = []
        
        for update in updates:
            try:
                product_key = update.get("product_key")
                if not product_key:
                    failed_count += 1
                    errors.append({"error": "Missing product_key", "data": update})
                    continue
                
                fields = update.get("fields", {})
                for field, value in fields.items():
                    self.update_product_field(product_key, field, value)
                
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({"error": str(e), "data": update})
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    def export_products(self, format: str = "json") -> str:
        """Export all products in specified format"""
        if format == "json":
            return json.dumps(list(self.products.values()), ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            if not self.products:
                return ""
            
            # Get all unique fields
            all_fields = set()
            for product in self.products.values():
                all_fields.update(product.keys())
            
            fieldnames = sorted(list(all_fields))
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in self.products.values():
                writer.writerow(product)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_statistics(self) -> Dict:
        """Get product statistics"""
        total = len(self.products)
        with_description = sum(1 for p in self.products.values() if p.get("description"))
        with_category = sum(1 for p in self.products.values() if p.get("category"))
        with_image = sum(1 for p in self.products.values() if p.get("image_url"))
        
        return {
            "total_products": total,
            "with_description": with_description,
            "with_category": with_category,
            "with_image": with_image,
            "completion_rate": round((with_description / total * 100) if total > 0 else 0, 2)
        }


# Global instance
_product_manager = None

def get_product_manager() -> ProductManager:
    """Get or create global ProductManager instance"""
    global _product_manager
    if _product_manager is None:
        _product_manager = ProductManager()
    return _product_manager
