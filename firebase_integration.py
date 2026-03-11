"""
Firebase Integration Module
Combines Clover API data with Firebase storage for unified product management
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from api_handler import CloverAPIHandler
from firebase_product_manager import get_firebase_product_manager
from firebase_storage_handler import get_storage_handler

logger = logging.getLogger(__name__)

class FirebaseIntegration:
    """Integrates Clover API with Firebase for product management"""
    
    def __init__(self):
        """Initialize Firebase integration"""
        self.firebase_pm = get_firebase_product_manager()
        self.storage = get_storage_handler()
        self.clover_api = None
    
    def _get_clover_api(self) -> Optional[CloverAPIHandler]:
        """Get Clover API handler (lazy initialization)"""
        if self.clover_api is None:
            try:
                self.clover_api = CloverAPIHandler()
            except Exception as e:
                logger.warning(f"Clover API not available: {e}")
                return None
        return self.clover_api
    
    def sync_clover_to_firebase(self, overwrite: bool = False) -> Dict:
        """
        Sync products from Clover API to Firebase
        
        Args:
            overwrite: If True, update existing products; if False, skip existing
        
        Returns:
            Sync result summary
        """
        try:
            clover = self._get_clover_api()
            if not clover:
                return {
                    'success': False,
                    'error': 'Clover API not configured',
                    'synced': 0,
                    'skipped': 0,
                    'failed': 0
                }
            
            # Fetch products from Clover
            logger.info("Fetching products from Clover API...")
            clover_products = clover.fetch_full_inventory()
            
            if not clover_products:
                return {
                    'success': False,
                    'error': 'No products found in Clover',
                    'synced': 0,
                    'skipped': 0,
                    'failed': 0
                }
            
            synced = 0
            skipped = 0
            failed = 0
            errors = []
            
            # Get existing Firebase products
            existing_products = self.firebase_pm.get_all_products(limit=10000)
            existing_ids = {p.get('clover_id') for p in existing_products if p.get('clover_id')}
            
            for clover_product in clover_products:
                try:
                    clover_id = clover_product.get('id')
                    
                    # Check if product already exists
                    if clover_id in existing_ids and not overwrite:
                        skipped += 1
                        continue
                    
                    # Prepare Firebase product data
                    firebase_data = {
                        'clover_id': clover_id,
                        'name': clover_product.get('name', ''),
                        'sku': clover_product.get('sku', ''),
                        'code': clover_product.get('code', ''),
                        'alt_code': clover_product.get('alt_code', ''),
                        'price': clover_product.get('price', 0),
                        'category': '',  # To be filled by user or AI
                        'description': '',  # To be filled by user or AI
                        'stock_quantity': 0,  # To be updated separately
                        'imageUrl': '',  # To be uploaded separately
                        'source': 'clover',
                        'last_synced': datetime.now().isoformat()
                    }
                    
                    if clover_id in existing_ids and overwrite:
                        # Update existing product
                        existing = next(p for p in existing_products if p.get('clover_id') == clover_id)
                        self.firebase_pm.update_product(existing['id'], firebase_data)
                    else:
                        # Create new product
                        self.firebase_pm.create_product(firebase_data)
                    
                    synced += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append({
                        'product': clover_product.get('name', 'Unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Failed to sync product {clover_product.get('name')}: {e}")
            
            logger.info(f"Sync complete: {synced} synced, {skipped} skipped, {failed} failed")
            
            return {
                'success': True,
                'synced': synced,
                'skipped': skipped,
                'failed': failed,
                'total': len(clover_products),
                'errors': errors[:10]  # Return first 10 errors
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'synced': 0,
                'skipped': 0,
                'failed': 0
            }
    
    def create_product_with_image(
        self,
        product_data: Dict,
        image_data: Optional[bytes] = None,
        image_filename: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create product with image upload
        
        Args:
            product_data: Product information
            image_data: Image file bytes
            image_filename: Original filename
        
        Returns:
            Created product with imageUrl or None
        """
        try:
            # Create product first to get ID
            product = self.firebase_pm.create_product(product_data)
            
            if not product:
                logger.error("Failed to create product")
                return None
            
            product_id = product['id']
            
            # Upload image if provided
            if image_data and image_filename:
                logger.info(f"Uploading image for product {product_id}...")
                image_url = self.storage.upload_image(
                    image_data=image_data,
                    filename=image_filename,
                    product_id=product_id,
                    compress=True
                )
                
                if image_url:
                    # Update product with image URL
                    product = self.firebase_pm.update_product(
                        product_id,
                        {'imageUrl': image_url}
                    )
                    logger.info(f"Image uploaded and linked to product {product_id}")
                else:
                    logger.warning(f"Image upload failed for product {product_id}")
            
            return product
            
        except Exception as e:
            logger.error(f"Failed to create product with image: {e}")
            return None
    
    def update_product_image(
        self,
        product_id: str,
        image_data: bytes,
        image_filename: str,
        delete_old: bool = True
    ) -> Optional[str]:
        """
        Update product image
        
        Args:
            product_id: Firebase product ID
            image_data: New image bytes
            image_filename: Filename
            delete_old: Whether to delete old image
        
        Returns:
            New image URL or None
        """
        try:
            # Get current product
            product = self.firebase_pm.get_product(product_id)
            if not product:
                logger.error(f"Product not found: {product_id}")
                return None
            
            # Delete old image if requested
            if delete_old and product.get('imageUrl'):
                self.storage.delete_image(product['imageUrl'])
            
            # Upload new image
            new_url = self.storage.upload_image(
                image_data=image_data,
                filename=image_filename,
                product_id=product_id,
                compress=True
            )
            
            if new_url:
                # Update product
                self.firebase_pm.update_product(product_id, {'imageUrl': new_url})
                logger.info(f"Product image updated: {product_id}")
            
            return new_url
            
        except Exception as e:
            logger.error(f"Failed to update product image: {e}")
            return None
    
    def get_products_with_filters(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        start_after: Optional[str] = None
    ) -> List[Dict]:
        """
        Get products with filters and pagination
        
        Args:
            category: Filter by category
            search: Search term
            limit: Max results
            start_after: Pagination cursor
        
        Returns:
            List of products
        """
        try:
            if category:
                products = self.firebase_pm.get_products_by_category(
                    category=category,
                    limit=limit,
                    start_after=start_after
                )
            elif search:
                products = self.firebase_pm.search_products(
                    search_term=search,
                    limit=limit
                )
            else:
                products = self.firebase_pm.get_all_products(
                    limit=limit,
                    start_after=start_after
                )
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return []
    
    def delete_product_with_image(self, product_id: str) -> bool:
        """
        Delete product and its associated image
        
        Args:
            product_id: Firebase product ID
        
        Returns:
            True if successful
        """
        try:
            # Get product
            product = self.firebase_pm.get_product(product_id)
            if not product:
                logger.error(f"Product not found: {product_id}")
                return False
            
            # Delete image if exists
            if product.get('imageUrl'):
                self.storage.delete_image(product['imageUrl'])
            
            # Delete product
            success = self.firebase_pm.delete_product(product_id)
            
            if success:
                logger.info(f"Product and image deleted: {product_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete product: {e}")
            return False


# Global instance
_firebase_integration = None

def get_firebase_integration() -> FirebaseIntegration:
    """Get or create global FirebaseIntegration instance"""
    global _firebase_integration
    if _firebase_integration is None:
        _firebase_integration = FirebaseIntegration()
    return _firebase_integration
