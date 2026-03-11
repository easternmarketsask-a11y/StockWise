"""
Firebase Product Manager
Manages product data in Firestore with CRUD operations and category filtering
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from firebase_config import get_firestore_client
from google.cloud.firestore_v1 import FieldFilter

logger = logging.getLogger(__name__)

class FirebaseProductManager:
    """Manages product data in Firestore"""
    
    COLLECTION_NAME = "products"
    
    def __init__(self):
        """Initialize Firestore product manager"""
        self.db = get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)
    
    def create_product(self, product_data: Dict) -> Optional[Dict]:
        """
        Create a new product in Firestore
        
        Args:
            product_data: Product information including:
                - name: str (required)
                - price: float
                - stock_quantity: int
                - category: str
                - description: str
                - sku: str
                - code: str
                - imageUrl: str (Cloud Storage URL)
        
        Returns:
            Created product with Firestore ID or None if failed
        """
        try:
            # Add timestamps
            now = datetime.now().isoformat()
            product_data['created_at'] = now
            product_data['updated_at'] = now
            
            # Validate required fields
            if 'name' not in product_data:
                raise ValueError("Product name is required")
            
            # Create document with auto-generated ID
            doc_ref = self.collection.document()
            product_data['id'] = doc_ref.id
            
            # Save to Firestore
            doc_ref.set(product_data)
            
            logger.info(f"Product created: {doc_ref.id}")
            return product_data
            
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            return None
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """
        Get product by ID
        
        Args:
            product_id: Firestore document ID
        
        Returns:
            Product data or None if not found
        """
        try:
            doc = self.collection.document(product_id).get()
            
            if doc.exists:
                product = doc.to_dict()
                product['id'] = doc.id
                return product
            else:
                logger.warning(f"Product not found: {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get product: {e}")
            return None
    
    def update_product(self, product_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update product fields
        
        Args:
            product_id: Firestore document ID
            updates: Fields to update
        
        Returns:
            Updated product or None if failed
        """
        try:
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            # Update document
            doc_ref = self.collection.document(product_id)
            doc_ref.update(updates)
            
            # Return updated product
            updated_product = self.get_product(product_id)
            logger.info(f"Product updated: {product_id}")
            
            return updated_product
            
        except Exception as e:
            logger.error(f"Failed to update product: {e}")
            return None
    
    def delete_product(self, product_id: str) -> bool:
        """
        Delete product from Firestore
        
        Args:
            product_id: Firestore document ID
        
        Returns:
            True if deleted successfully
        """
        try:
            self.collection.document(product_id).delete()
            logger.info(f"Product deleted: {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete product: {e}")
            return False
    
    def get_all_products(
        self,
        limit: int = 100,
        start_after: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all products with pagination
        
        Args:
            limit: Maximum number of products to return
            start_after: Document ID to start after (for pagination)
        
        Returns:
            List of products
        """
        try:
            query = self.collection.order_by('created_at').limit(limit)
            
            # Pagination support
            if start_after:
                start_doc = self.collection.document(start_after).get()
                if start_doc.exists:
                    query = query.start_after(start_doc)
            
            docs = query.stream()
            
            products = []
            for doc in docs:
                product = doc.to_dict()
                product['id'] = doc.id
                products.append(product)
            
            logger.info(f"Retrieved {len(products)} products")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return []
    
    def get_products_by_category(
        self,
        category: str,
        limit: int = 100,
        start_after: Optional[str] = None
    ) -> List[Dict]:
        """
        Get products filtered by category with pagination
        
        Args:
            category: Category name to filter
            limit: Maximum number of products
            start_after: Document ID for pagination
        
        Returns:
            List of products in the category
        """
        try:
            query = self.collection.where(
                filter=FieldFilter('category', '==', category)
            ).order_by('created_at').limit(limit)
            
            # Pagination support
            if start_after:
                start_doc = self.collection.document(start_after).get()
                if start_doc.exists:
                    query = query.start_after(start_doc)
            
            docs = query.stream()
            
            products = []
            for doc in docs:
                product = doc.to_dict()
                product['id'] = doc.id
                products.append(product)
            
            logger.info(f"Retrieved {len(products)} products in category '{category}'")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products by category: {e}")
            return []
    
    def search_products(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search products by name (simple text search)
        
        Note: For advanced full-text search, consider using Algolia or Elasticsearch
        
        Args:
            search_term: Text to search in product name
            limit: Maximum results
        
        Returns:
            List of matching products
        """
        try:
            # Get all products (in production, use proper search service)
            all_products = self.get_all_products(limit=1000)
            
            # Filter by search term (case-insensitive)
            search_lower = search_term.lower()
            results = [
                p for p in all_products
                if search_lower in p.get('name', '').lower()
                or search_lower in p.get('sku', '').lower()
                or search_lower in p.get('code', '').lower()
            ]
            
            logger.info(f"Search '{search_term}' found {len(results)} products")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to search products: {e}")
            return []
    
    def get_categories(self) -> List[str]:
        """
        Get all unique categories
        
        Returns:
            List of category names
        """
        try:
            # Get all products
            products = self.get_all_products(limit=10000)
            
            # Extract unique categories
            categories = set()
            for product in products:
                category = product.get('category')
                if category:
                    categories.add(category)
            
            category_list = sorted(list(categories))
            logger.info(f"Found {len(category_list)} categories")
            
            return category_list
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get product statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            products = self.get_all_products(limit=10000)
            
            total = len(products)
            with_image = sum(1 for p in products if p.get('imageUrl'))
            with_description = sum(1 for p in products if p.get('description'))
            categories = len(self.get_categories())
            
            total_stock = sum(p.get('stock_quantity', 0) for p in products)
            total_value = sum(
                p.get('price', 0) * p.get('stock_quantity', 0)
                for p in products
            )
            
            return {
                'total_products': total,
                'with_image': with_image,
                'with_description': with_description,
                'total_categories': categories,
                'total_stock_quantity': total_stock,
                'total_inventory_value': round(total_value, 2),
                'completion_rate': round((with_description / total * 100) if total > 0 else 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def bulk_create(self, products: List[Dict]) -> Dict:
        """
        Bulk create multiple products
        
        Args:
            products: List of product data dictionaries
        
        Returns:
            Result summary with success/failure counts
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for product_data in products:
            try:
                result = self.create_product(product_data)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append({
                        'product': product_data.get('name', 'Unknown'),
                        'error': 'Creation failed'
                    })
            except Exception as e:
                failed_count += 1
                errors.append({
                    'product': product_data.get('name', 'Unknown'),
                    'error': str(e)
                })
        
        logger.info(f"Bulk create: {success_count} success, {failed_count} failed")
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors
        }


# Global instance
_firebase_product_manager = None

def get_firebase_product_manager() -> FirebaseProductManager:
    """Get or create global FirebaseProductManager instance"""
    global _firebase_product_manager
    if _firebase_product_manager is None:
        _firebase_product_manager = FirebaseProductManager()
    return _firebase_product_manager
