"""
AI Results Store Module - Persistent storage for AI processing results
Stores and manages AI-generated classifications, descriptions, recipes, and images
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AIResultsStore:
    """Manages AI processing results storage and editing"""
    
    def __init__(self, storage_path: str = "data/ai_results.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Dict] = {}
        self._load_results()
    
    def _load_results(self):
        """Load AI results from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
                logger.info(f"Loaded {len(self.results)} AI results from storage")
            except Exception as e:
                logger.error(f"Failed to load AI results: {e}")
                self.results = {}
        else:
            self.results = {}
    
    def _save_results(self):
        """Save AI results to storage"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.results)} AI results to storage")
            return True
        except Exception as e:
            logger.error(f"Failed to save AI results: {e}")
            return False
    
    def get_result_key(self, product_id: str = None, name: str = None, sku: str = None, code: str = None) -> str:
        """Generate unique result key matching product key"""
        if product_id:
            return f"id_{product_id}"
        return f"key_{name}_{sku}_{code}"
    
    def save_classification(self, product_info: Dict, classification: Dict) -> Dict:
        """Save AI classification result"""
        key = self.get_result_key(
            product_info.get("id"),
            product_info.get("name"),
            product_info.get("sku"),
            product_info.get("code")
        )
        
        if key not in self.results:
            self.results[key] = {
                "product_info": product_info,
                "created_at": datetime.now().isoformat()
            }
        
        self.results[key]["classification"] = classification
        self.results[key]["classification_updated_at"] = datetime.now().isoformat()
        self.results[key]["updated_at"] = datetime.now().isoformat()
        
        self._save_results()
        return self.results[key]
    
    def save_description(self, product_info: Dict, description: Dict) -> Dict:
        """Save AI description result"""
        key = self.get_result_key(
            product_info.get("id"),
            product_info.get("name"),
            product_info.get("sku"),
            product_info.get("code")
        )
        
        if key not in self.results:
            self.results[key] = {
                "product_info": product_info,
                "created_at": datetime.now().isoformat()
            }
        
        self.results[key]["description"] = description
        self.results[key]["description_updated_at"] = datetime.now().isoformat()
        self.results[key]["updated_at"] = datetime.now().isoformat()
        
        self._save_results()
        return self.results[key]
    
    def save_recipe(self, product_info: Dict, recipe: Dict) -> Dict:
        """Save AI recipe recommendation result"""
        key = self.get_result_key(
            product_info.get("id"),
            product_info.get("name"),
            product_info.get("sku"),
            product_info.get("code")
        )
        
        if key not in self.results:
            self.results[key] = {
                "product_info": product_info,
                "created_at": datetime.now().isoformat()
            }
        
        self.results[key]["recipe"] = recipe
        self.results[key]["recipe_updated_at"] = datetime.now().isoformat()
        self.results[key]["updated_at"] = datetime.now().isoformat()
        
        self._save_results()
        return self.results[key]
    
    def save_image_info(self, product_info: Dict, image_info: Dict) -> Dict:
        """Save AI-generated image information"""
        key = self.get_result_key(
            product_info.get("id"),
            product_info.get("name"),
            product_info.get("sku"),
            product_info.get("code")
        )
        
        if key not in self.results:
            self.results[key] = {
                "product_info": product_info,
                "created_at": datetime.now().isoformat()
            }
        
        self.results[key]["image_info"] = image_info
        self.results[key]["image_updated_at"] = datetime.now().isoformat()
        self.results[key]["updated_at"] = datetime.now().isoformat()
        
        self._save_results()
        return self.results[key]
    
    def get_result(self, product_key: str) -> Optional[Dict]:
        """Get AI result by product key"""
        return self.results.get(product_key)
    
    def update_result_field(self, product_key: str, result_type: str, field: str, value) -> Optional[Dict]:
        """Update a specific field in an AI result
        
        Args:
            product_key: Product identifier
            result_type: Type of result (classification, description, recipe, image_info)
            field: Field name to update
            value: New value
        """
        if product_key not in self.results:
            return None
        
        if result_type not in self.results[product_key]:
            self.results[product_key][result_type] = {}
        
        self.results[product_key][result_type][field] = value
        self.results[product_key]["updated_at"] = datetime.now().isoformat()
        self.results[product_key][f"{result_type}_updated_at"] = datetime.now().isoformat()
        
        self._save_results()
        return self.results[product_key]
    
    def delete_result(self, product_key: str) -> bool:
        """Delete an AI result"""
        if product_key in self.results:
            del self.results[product_key]
            self._save_results()
            return True
        return False
    
    def get_all_results(self, filters: Dict = None) -> List[Dict]:
        """Get all AI results with optional filters"""
        results = list(self.results.values())
        
        if not filters:
            return results
        
        filtered = results
        
        if "has_classification" in filters:
            if filters["has_classification"]:
                filtered = [r for r in filtered if "classification" in r]
            else:
                filtered = [r for r in filtered if "classification" not in r]
        
        if "has_description" in filters:
            if filters["has_description"]:
                filtered = [r for r in filtered if "description" in r]
            else:
                filtered = [r for r in filtered if "description" not in r]
        
        if "has_recipe" in filters:
            if filters["has_recipe"]:
                filtered = [r for r in filtered if "recipe" in r]
            else:
                filtered = [r for r in filtered if "recipe" not in r]
        
        if "has_image" in filters:
            if filters["has_image"]:
                filtered = [r for r in filtered if "image_info" in r]
            else:
                filtered = [r for r in filtered if "image_info" not in r]
        
        if "category" in filters:
            filtered = [r for r in filtered 
                       if r.get("classification", {}).get("main_category") == filters["category"]]
        
        if "search" in filters:
            search_term = filters["search"].lower()
            filtered = [r for r in filtered 
                       if search_term in r.get("product_info", {}).get("name", "").lower()]
        
        return filtered
    
    def export_results(self, format: str = "json", result_types: List[str] = None) -> str:
        """Export AI results in specified format
        
        Args:
            format: Export format (json, csv)
            result_types: List of result types to include (classification, description, recipe, image_info)
        """
        if format == "json":
            if result_types:
                filtered_results = []
                for result in self.results.values():
                    filtered = {"product_info": result.get("product_info")}
                    for rt in result_types:
                        if rt in result:
                            filtered[rt] = result[rt]
                    filtered_results.append(filtered)
                return json.dumps(filtered_results, ensure_ascii=False, indent=2)
            else:
                return json.dumps(list(self.results.values()), ensure_ascii=False, indent=2)
        
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            if not self.results:
                return ""
            
            # Define CSV columns
            fieldnames = [
                "product_name", "sku", "code", "price",
                "main_category", "sub_category", "attributes",
                "description", "keywords", "selling_points",
                "recipe_name", "recipe_ingredients",
                "image_url", "created_at", "updated_at"
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results.values():
                product = result.get("product_info", {})
                classification = result.get("classification", {})
                description = result.get("description", {})
                recipe = result.get("recipe", {})
                image = result.get("image_info", {})
                
                row = {
                    "product_name": product.get("name", ""),
                    "sku": product.get("sku", ""),
                    "code": product.get("code", ""),
                    "price": product.get("price", ""),
                    "main_category": classification.get("main_category", ""),
                    "sub_category": classification.get("sub_category", ""),
                    "attributes": ", ".join(classification.get("attributes", [])),
                    "description": description.get("description", ""),
                    "keywords": ", ".join(description.get("keywords", [])),
                    "selling_points": " | ".join(description.get("selling_points", [])),
                    "recipe_name": recipe.get("recipe_name", ""),
                    "recipe_ingredients": ", ".join(recipe.get("ingredients", [])),
                    "image_url": image.get("url", ""),
                    "created_at": result.get("created_at", ""),
                    "updated_at": result.get("updated_at", "")
                }
                writer.writerow(row)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_statistics(self) -> Dict:
        """Get AI results statistics"""
        total = len(self.results)
        with_classification = sum(1 for r in self.results.values() if "classification" in r)
        with_description = sum(1 for r in self.results.values() if "description" in r)
        with_recipe = sum(1 for r in self.results.values() if "recipe" in r)
        with_image = sum(1 for r in self.results.values() if "image_info" in r)
        
        return {
            "total_results": total,
            "with_classification": with_classification,
            "with_description": with_description,
            "with_recipe": with_recipe,
            "with_image": with_image,
            "classification_rate": round((with_classification / total * 100) if total > 0 else 0, 2),
            "description_rate": round((with_description / total * 100) if total > 0 else 0, 2),
            "recipe_rate": round((with_recipe / total * 100) if total > 0 else 0, 2),
            "image_rate": round((with_image / total * 100) if total > 0 else 0, 2)
        }
    
    def merge_with_products(self, products: List[Dict]) -> List[Dict]:
        """Merge AI results with product list"""
        merged = []
        for product in products:
            key = self.get_result_key(
                product.get("id"),
                product.get("name"),
                product.get("sku"),
                product.get("code")
            )
            
            result = self.results.get(key, {})
            merged_item = {**product}
            
            if "classification" in result:
                merged_item["ai_classification"] = result["classification"]
            if "description" in result:
                merged_item["ai_description"] = result["description"]
            if "recipe" in result:
                merged_item["ai_recipe"] = result["recipe"]
            if "image_info" in result:
                merged_item["ai_image"] = result["image_info"]
            
            merged.append(merged_item)
        
        return merged


# Global instance
_ai_results_store = None

def get_ai_results_store() -> AIResultsStore:
    """Get or create global AIResultsStore instance"""
    global _ai_results_store
    if _ai_results_store is None:
        _ai_results_store = AIResultsStore()
    return _ai_results_store
