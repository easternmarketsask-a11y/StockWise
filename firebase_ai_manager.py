"""
Firebase AI Results Manager
Manages AI processing results (classification and description) in Firestore
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from firebase_config import get_firestore_client
from google.cloud.firestore_v1 import FieldFilter

logger = logging.getLogger(__name__)

class FirebaseAIManager:
    """Manages AI processing results in Firestore"""
    
    COLLECTION_NAME = "ai_results"
    
    def __init__(self):
        """Initialize Firestore AI manager"""
        self.db = get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)
    
    def _normalize_product_data(self, product: Dict) -> Dict:
        """Normalize product data field names for Firestore compatibility"""
        # Map Chinese field names to English equivalents
        field_mapping = {
            '商品信息': 'product_name',
            '商品名称': 'product_name',
            'Product Code': 'product_code',
            'SKU': 'sku'
        }
        
        normalized = {}
        for key, value in product.items():
            # Use mapped field name or keep original
            normalized_key = field_mapping.get(key, key)
            normalized[normalized_key] = value
            logger.info(f"Mapped field: {key} -> {normalized_key}")
        
        logger.info(f"Normalized product data: {normalized}")
        return normalized
    
    def _generate_product_key(self, product: Dict) -> str:
        """Generate unique key for product based on name, SKU, and code"""
        # Try multiple possible field names for product name
        name = (
            str(product.get('商品信息', '')).strip().lower() or
            str(product.get('name', '')).strip().lower() or
            str(product.get('product_name', '')).strip().lower() or
            str(product.get('商品名称', '')).strip().lower()
        )
        sku = str(product.get('SKU', '')).strip().lower() or str(product.get('sku', '')).strip().lower()
        code = str(product.get('Product Code', '')).strip().lower() or str(product.get('product_code', '')).strip().lower()
        return f"{name}|{sku}|{code}"
    
    def save_ai_result(self, product: Dict, result_type: str, result_data: Dict) -> Optional[Dict]:
        """
        Save AI processing result to Firestore
        
        Args:
            product: Product information
            result_type: 'classify' or 'describe'
            result_data: AI processing result
            
        Returns:
            Saved result document or None if failed
        """
        try:
            product_key = self._generate_product_key(product)
            logger.info(f"Generated product key: {product_key}")
            logger.info(f"Product data: {product}")
            
            # Normalize product data for Firestore
            normalized_product = self._normalize_product_data(product)
            
            # Check if result already exists
            existing = self.get_ai_result(product, result_type)
            if existing:
                # Update existing result
                doc_ref = self.collection.document(existing['id'])
                doc_ref.update({
                    'result': result_data,
                    'updated_at': datetime.utcnow().isoformat(),
                    'product_data': normalized_product  # Use normalized data
                })
                logger.info(f"Updated AI {result_type} result for product: {product_key}")
                return self.get_ai_result(product, result_type)
            
            # Create new result
            ai_result = {
                'product_key': product_key,
                'result_type': result_type,
                'result': result_data,
                'product_data': normalized_product,  # Use normalized data
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            doc_ref = self.collection.document()
            doc_ref.set(ai_result)
            
            ai_result['id'] = doc_ref.id
            logger.info(f"Saved AI {result_type} result for product: {product_key}")
            return ai_result
            
        except Exception as e:
            logger.error(f"Error saving AI result: {e}")
            return None
    
    def get_ai_result(self, product: Dict, result_type: str) -> Optional[Dict]:
        """
        Get AI processing result for a product
        
        Args:
            product: Product information
            result_type: 'classify' or 'describe'
            
        Returns:
            AI result document or None if not found
        """
        try:
            product_key = self._generate_product_key(product)
            
            query = self.collection.where(
                filter=FieldFilter('product_key', '==', product_key)
            ).where(
                filter=FieldFilter('result_type', '==', result_type)
            ).limit(1)
            
            docs = list(query.stream())
            
            if docs:
                doc = docs[0]
                result = doc.to_dict()
                result['id'] = doc.id
                return result
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting AI result: {e}")
            return None
    
    def get_all_ai_results(self, result_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get all AI results, optionally filtered by type
        
        Args:
            result_type: 'classify', 'describe', or None for all
            limit: Maximum number of results to return
            
        Returns:
            List of AI result documents
        """
        try:
            query = self.collection.order_by('created_at', direction='DESCENDING')
            
            if result_type:
                query = query.where(filter=FieldFilter('result_type', '==', result_type))
            
            query = query.limit(limit)
            
            results = []
            for doc in query.stream():
                result = doc.to_dict()
                result['id'] = doc.id
                results.append(result)
            
            logger.info(f"Retrieved {len(results)} AI results")
            return results
            
        except Exception as e:
            logger.error(f"Error getting AI results: {e}")
            return []
    
    def get_ai_statistics(self) -> Dict:
        """
        Get statistics about AI processing results
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get all results
            all_results = self.get_all_ai_results(limit=1000)
            
            classify_count = len([r for r in all_results if r['result_type'] == 'classify'])
            describe_count = len([r for r in all_results if r['result_type'] == 'describe'])
            
            # Get unique products
            unique_products = set(r['product_key'] for r in all_results)
            
            # Get products with both classification and description
            products_with_both = 0
            for product_key in unique_products:
                product_results = [r for r in all_results if r['product_key'] == product_key]
                types = set(r['result_type'] for r in product_results)
                if len(types) == 2:  # Both classify and describe
                    products_with_both += 1
            
            return {
                'total_results': len(all_results),
                'classify_results': classify_count,
                'describe_results': describe_count,
                'unique_products': len(unique_products),
                'products_with_both': products_with_both,
                'completion_rate': (products_with_both / len(unique_products) * 100) if unique_products else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting AI statistics: {e}")
            return {
                'total_results': 0,
                'classify_results': 0,
                'describe_results': 0,
                'unique_products': 0,
                'products_with_both': 0,
                'completion_rate': 0
            }
    
    def delete_ai_result(self, product: Dict, result_type: str) -> bool:
        """
        Delete AI processing result for a product
        
        Args:
            product: Product information
            result_type: 'classify' or 'describe'
            
        Returns:
            True if deleted, False if not found or failed
        """
        try:
            result = self.get_ai_result(product, result_type)
            if result:
                self.collection.document(result['id']).delete()
                logger.info(f"Deleted AI {result_type} result for product")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting AI result: {e}")
            return False
    
    def batch_get_ai_results(self, products: List[Dict], result_type: str) -> Dict[str, Optional[Dict]]:
        """
        Batch get AI results for multiple products
        
        Args:
            products: List of product dictionaries
            result_type: 'classify' or 'describe'
            
        Returns:
            Dictionary mapping product keys to AI results
        """
        results = {}
        for product in products:
            product_key = self._generate_product_key(product)
            result = self.get_ai_result(product, result_type)
            results[product_key] = result
        return results
