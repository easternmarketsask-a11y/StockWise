"""
Firebase Cloud Storage Handler
Handles image upload, compression, and retrieval from Cloud Storage
"""
import os
import io
import logging
import uuid
from typing import Optional, Tuple
from datetime import timedelta
from PIL import Image
from firebase_config import get_storage_bucket

logger = logging.getLogger(__name__)

class StorageHandler:
    """Handles Cloud Storage operations for product images"""
    
    def __init__(self, bucket_folder: str = "products"):
        """
        Initialize storage handler
        
        Args:
            bucket_folder: Folder path in the bucket for organizing files
        """
        self.bucket_folder = bucket_folder
        self.bucket = get_storage_bucket()
    
    def compress_image(
        self, 
        image_data: bytes, 
        max_size: Tuple[int, int] = (1200, 1200),
        quality: int = 85
    ) -> bytes:
        """
        Compress image before upload
        
        Args:
            image_data: Original image bytes
            max_size: Maximum dimensions (width, height)
            quality: JPEG quality (1-100)
        
        Returns:
            Compressed image bytes
        """
        try:
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if larger than max_size
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = output.getvalue()
            
            original_size = len(image_data)
            compressed_size = len(compressed_data)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Image compressed: {original_size} -> {compressed_size} bytes ({compression_ratio:.1f}% reduction)")
            
            return compressed_data
            
        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return image_data
    
    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        product_id: str,
        compress: bool = True,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Upload image to Cloud Storage
        
        Args:
            image_data: Image file bytes
            filename: Original filename
            product_id: Product ID for organizing files
            compress: Whether to compress before upload
            content_type: MIME type
        
        Returns:
            Public URL of uploaded image or None if failed
        """
        try:
            # Compress image if requested
            if compress:
                image_data = self.compress_image(image_data)
            
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1] or '.jpg'
            unique_filename = f"{product_id}_{uuid.uuid4().hex[:8]}{file_extension}"
            blob_path = f"{self.bucket_folder}/{unique_filename}"
            
            # Upload to Cloud Storage
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                image_data,
                content_type=content_type
            )
            
            # Make blob publicly accessible
            blob.make_public()
            
            # Get public URL
            public_url = blob.public_url
            
            logger.info(f"Image uploaded successfully: {blob_path}")
            logger.info(f"Public URL: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            return None
    
    def upload_image_from_file(
        self,
        file_path: str,
        product_id: str,
        compress: bool = True
    ) -> Optional[str]:
        """
        Upload image from local file path
        
        Args:
            file_path: Path to local image file
            product_id: Product ID
            compress: Whether to compress
        
        Returns:
            Public URL or None
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            filename = os.path.basename(file_path)
            return self.upload_image(image_data, filename, product_id, compress)
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from Cloud Storage
        
        Args:
            image_url: Public URL of the image
        
        Returns:
            True if deleted successfully
        """
        try:
            # Extract blob path from URL
            # URL format: https://storage.googleapis.com/bucket-name/path/to/file
            if 'storage.googleapis.com' in image_url:
                parts = image_url.split('/')
                blob_path = '/'.join(parts[4:])  # Skip protocol, domain, bucket
            else:
                logger.error(f"Invalid image URL format: {image_url}")
                return False
            
            # Delete blob
            blob = self.bucket.blob(blob_path)
            blob.delete()
            
            logger.info(f"Image deleted: {blob_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            return False
    
    def get_signed_url(self, blob_path: str, expiration_minutes: int = 60) -> Optional[str]:
        """
        Generate signed URL for temporary access
        
        Args:
            blob_path: Path to blob in bucket
            expiration_minutes: URL expiration time in minutes
        
        Returns:
            Signed URL or None
        """
        try:
            blob = self.bucket.blob(blob_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None
    
    def list_product_images(self, product_id: str) -> list:
        """
        List all images for a product
        
        Args:
            product_id: Product ID
        
        Returns:
            List of public URLs
        """
        try:
            prefix = f"{self.bucket_folder}/{product_id}_"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            urls = [blob.public_url for blob in blobs]
            logger.info(f"Found {len(urls)} images for product {product_id}")
            
            return urls
            
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []


# Global instance
_storage_handler = None

def get_storage_handler() -> StorageHandler:
    """Get or create global StorageHandler instance"""
    global _storage_handler
    if _storage_handler is None:
        _storage_handler = StorageHandler()
    return _storage_handler
