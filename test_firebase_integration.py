"""
Firebase Integration Test Script
Tests all Firebase functionality including Firestore and Cloud Storage
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_firebase_initialization():
    """Test Firebase initialization"""
    print("\n=== Testing Firebase Initialization ===")
    try:
        from firebase_config import FirebaseConfig
        FirebaseConfig.initialize()
        
        db = FirebaseConfig.get_db()
        bucket = FirebaseConfig.get_bucket()
        
        print("✅ Firebase initialized successfully")
        print(f"✅ Firestore client: {type(db).__name__}")
        print(f"✅ Storage bucket: {bucket.name}")
        return True
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False


def test_product_manager():
    """Test Firestore product manager"""
    print("\n=== Testing Firestore Product Manager ===")
    try:
        from firebase_product_manager import get_firebase_product_manager
        
        pm = get_firebase_product_manager()
        
        # Create test product
        test_product = {
            "name": "测试商品 - Firebase集成测试",
            "price": 99.99,
            "stock_quantity": 50,
            "category": "测试分类",
            "description": "这是一个测试商品，用于验证Firebase集成",
            "sku": "TEST-SKU-001",
            "code": "TEST-BARCODE-001"
        }
        
        print("Creating test product...")
        product = pm.create_product(test_product)
        if not product:
            print("❌ Failed to create product")
            return False
        
        product_id = product['id']
        print(f"✅ Product created with ID: {product_id}")
        
        # Read product
        print("Reading product...")
        retrieved = pm.get_product(product_id)
        if not retrieved:
            print("❌ Failed to retrieve product")
            return False
        print(f"✅ Product retrieved: {retrieved['name']}")
        
        # Update product
        print("Updating product...")
        updated = pm.update_product(product_id, {"price": 79.99})
        if not updated or updated['price'] != 79.99:
            print("❌ Failed to update product")
            return False
        print(f"✅ Product updated: price = {updated['price']}")
        
        # Get all products
        print("Getting all products...")
        products = pm.get_all_products(limit=10)
        print(f"✅ Retrieved {len(products)} products")
        
        # Get statistics
        print("Getting statistics...")
        stats = pm.get_statistics()
        print(f"✅ Statistics: {stats}")
        
        # Delete product
        print("Deleting test product...")
        deleted = pm.delete_product(product_id)
        if not deleted:
            print("❌ Failed to delete product")
            return False
        print("✅ Product deleted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Product manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_handler():
    """Test Cloud Storage handler"""
    print("\n=== Testing Cloud Storage Handler ===")
    try:
        from firebase_storage_handler import get_storage_handler
        from PIL import Image
        import io
        
        storage = get_storage_handler()
        
        # Create test image
        print("Creating test image...")
        img = Image.new('RGB', (800, 600), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        print(f"✅ Test image created: {len(image_data)} bytes")
        
        # Upload image
        print("Uploading image...")
        image_url = storage.upload_image(
            image_data=image_data,
            filename="test_image.jpg",
            product_id="test_product_123",
            compress=True
        )
        
        if not image_url:
            print("❌ Failed to upload image")
            return False
        
        print(f"✅ Image uploaded: {image_url}")
        
        # List product images
        print("Listing product images...")
        urls = storage.list_product_images("test_product_123")
        print(f"✅ Found {len(urls)} images for product")
        
        # Delete image
        print("Deleting test image...")
        deleted = storage.delete_image(image_url)
        if not deleted:
            print("⚠️  Warning: Failed to delete image (may need manual cleanup)")
        else:
            print("✅ Image deleted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test Firebase integration module"""
    print("\n=== Testing Firebase Integration ===")
    try:
        from firebase_integration import get_firebase_integration
        
        integration = get_firebase_integration()
        
        # Test product creation with image
        print("Testing product creation with image...")
        from PIL import Image
        import io
        
        # Create test image
        img = Image.new('RGB', (600, 400), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        
        product_data = {
            "name": "集成测试商品",
            "price": 49.99,
            "category": "集成测试",
            "stock_quantity": 25
        }
        
        product = integration.create_product_with_image(
            product_data=product_data,
            image_data=image_data,
            image_filename="integration_test.jpg"
        )
        
        if not product:
            print("❌ Failed to create product with image")
            return False
        
        product_id = product['id']
        print(f"✅ Product created with image: {product_id}")
        print(f"✅ Image URL: {product.get('imageUrl', 'N/A')}")
        
        # Test filtering
        print("Testing product filtering...")
        filtered = integration.get_products_with_filters(
            category="集成测试",
            limit=10
        )
        print(f"✅ Found {len(filtered)} products in category")
        
        # Clean up
        print("Cleaning up test product...")
        deleted = integration.delete_product_with_image(product_id)
        if deleted:
            print("✅ Test product and image deleted")
        else:
            print("⚠️  Warning: Failed to delete test product")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clover_sync():
    """Test Clover to Firebase sync"""
    print("\n=== Testing Clover Sync (Optional) ===")
    try:
        from firebase_integration import get_firebase_integration
        
        integration = get_firebase_integration()
        
        print("Attempting to sync from Clover API...")
        result = integration.sync_clover_to_firebase(overwrite=False)
        
        if result['success']:
            print(f"✅ Sync successful:")
            print(f"   - Synced: {result['synced']}")
            print(f"   - Skipped: {result['skipped']}")
            print(f"   - Failed: {result['failed']}")
            print(f"   - Total: {result['total']}")
        else:
            print(f"⚠️  Sync failed: {result.get('error', 'Unknown error')}")
            print("   This is expected if Clover API is not configured")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Clover sync test failed: {e}")
        print("   This is expected if Clover API is not configured")
        return True  # Don't fail the test suite


def main():
    """Run all tests"""
    print("=" * 60)
    print("Firebase Integration Test Suite")
    print("=" * 60)
    
    # Check environment variables
    print("\n=== Environment Check ===")
    firebase_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
    firebase_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")
    
    print(f"FIREBASE_SERVICE_ACCOUNT_PATH: {'✅ Set' if firebase_path else '❌ Not set'}")
    print(f"FIREBASE_SERVICE_ACCOUNT_JSON: {'✅ Set' if firebase_json else '❌ Not set'}")
    print(f"FIREBASE_STORAGE_BUCKET: {storage_bucket or '❌ Not set'}")
    
    if not (firebase_path or firebase_json):
        print("\n❌ ERROR: Firebase credentials not configured!")
        print("Please set FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON")
        return False
    
    # Run tests
    results = {
        "Firebase Initialization": test_firebase_initialization(),
        "Product Manager": test_product_manager(),
        "Storage Handler": test_storage_handler(),
        "Integration": test_integration(),
        "Clover Sync": test_clover_sync()
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
