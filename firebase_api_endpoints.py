"""
Firebase API Endpoints for FastAPI
RESTful API endpoints for Firebase product management
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional, Dict, List
import logging
from firebase_integration import get_firebase_integration
from firebase_product_manager import get_firebase_product_manager
from firebase_ai_manager import FirebaseAIManager

logger = logging.getLogger(__name__)

# Create API router
firebase_router = APIRouter(prefix="/api/firebase", tags=["Firebase"])

# Get instances
integration = get_firebase_integration()
pm = get_firebase_product_manager()
ai_manager = FirebaseAIManager()


@firebase_router.post("/products")
async def create_product(product_data: Dict):
    """
    Create a new product in Firestore
    
    Request body:
    {
        "name": "商品名称",
        "price": 29.99,
        "stock_quantity": 100,
        "category": "水果",
        "description": "商品描述",
        "sku": "SKU-123",
        "code": "BARCODE"
    }
    """
    try:
        product = pm.create_product(product_data)
        if product:
            return {
                "success": True,
                "product": product,
                "message": "Product created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create product")
    except Exception as e:
        logger.error(f"Create product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/products")
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    start_after: Optional[str] = Query(None, description="Pagination cursor")
):
    """
    Get products with filters and pagination
    
    Query parameters:
    - category: Filter by category name
    - search: Search in name, SKU, code
    - limit: Maximum number of results (1-1000)
    - start_after: Document ID to start after (for pagination)
    """
    try:
        products = integration.get_products_with_filters(
            category=category,
            search=search,
            limit=limit,
            start_after=start_after
        )
        
        return {
            "success": True,
            "products": products,
            "count": len(products),
            "has_more": len(products) == limit
        }
    except Exception as e:
        logger.error(f"Get products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get a single product by ID"""
    try:
        product = pm.get_product(product_id)
        if product:
            return {
                "success": True,
                "product": product
            }
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        logger.error(f"Get product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.put("/products/{product_id}")
async def update_product(product_id: str, updates: Dict):
    """
    Update product fields
    
    Request body:
    {
        "price": 35.99,
        "stock_quantity": 150,
        "description": "Updated description"
    }
    """
    try:
        product = pm.update_product(product_id, updates)
        if product:
            return {
                "success": True,
                "product": product,
                "message": "Product updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        logger.error(f"Update product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete product and associated image"""
    try:
        success = integration.delete_product_with_image(product_id)
        if success:
            return {
                "success": True,
                "message": "Product and image deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        logger.error(f"Delete product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.post("/products/{product_id}/image")
async def upload_product_image(
    product_id: str,
    image: UploadFile = File(...),
    delete_old: bool = Form(True)
):
    """
    Upload or update product image
    
    Form data:
    - image: Image file (JPEG, PNG, etc.)
    - delete_old: Whether to delete old image (default: true)
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Upload image
        image_url = integration.update_product_image(
            product_id=product_id,
            image_data=image_data,
            image_filename=image.filename,
            delete_old=delete_old
        )
        
        if image_url:
            return {
                "success": True,
                "imageUrl": image_url,
                "message": "Image uploaded successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload image")
    except Exception as e:
        logger.error(f"Upload image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.post("/products/create-with-image")
async def create_product_with_image(
    name: str = Form(...),
    price: float = Form(...),
    stock_quantity: int = Form(0),
    category: str = Form(""),
    description: str = Form(""),
    sku: str = Form(""),
    code: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    """
    Create product with image upload in one request
    
    Form data:
    - name: Product name (required)
    - price: Product price (required)
    - stock_quantity: Stock quantity
    - category: Category name
    - description: Product description
    - sku: SKU code
    - code: Barcode
    - image: Product image file (optional)
    """
    try:
        # Prepare product data
        product_data = {
            "name": name,
            "price": price,
            "stock_quantity": stock_quantity,
            "category": category,
            "description": description,
            "sku": sku,
            "code": code
        }
        
        # Read image if provided
        image_data = None
        image_filename = None
        if image:
            image_data = await image.read()
            image_filename = image.filename
        
        # Create product with image
        product = integration.create_product_with_image(
            product_data=product_data,
            image_data=image_data,
            image_filename=image_filename
        )
        
        if product:
            return {
                "success": True,
                "product": product,
                "message": "Product created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create product")
    except Exception as e:
        logger.error(f"Create product with image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.post("/sync-clover")
async def sync_clover_products(overwrite: bool = Query(False)):
    """
    Sync products from Clover API to Firebase
    
    Query parameters:
    - overwrite: If true, update existing products; if false, skip existing
    """
    try:
        result = integration.sync_clover_to_firebase(overwrite=overwrite)
        
        if result['success']:
            return {
                "success": True,
                "result": result,
                "message": f"Synced {result['synced']} products from Clover"
            }
        else:
            return {
                "success": False,
                "result": result,
                "message": result.get('error', 'Sync failed')
            }
    except Exception as e:
        logger.error(f"Sync Clover error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/categories")
async def get_categories():
    """Get all unique product categories"""
    try:
        categories = pm.get_categories()
        return {
            "success": True,
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        logger.error(f"Get categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/categories/{category_name}")
async def get_products_by_category(
    category_name: str,
    limit: int = Query(100, ge=1, le=1000),
    start_after: Optional[str] = Query(None)
):
    """Get products in a specific category with pagination"""
    try:
        products = pm.get_products_by_category(
            category=category_name,
            limit=limit,
            start_after=start_after
        )
        
        return {
            "success": True,
            "category": category_name,
            "products": products,
            "count": len(products),
            "has_more": len(products) == limit
        }
    except Exception as e:
        logger.error(f"Get category products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/statistics")
async def get_statistics():
    """Get product statistics"""
    try:
        stats = pm.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.post("/products/bulk-create")
async def bulk_create_products(products: List[Dict]):
    """
    Bulk create multiple products
    
    Request body:
    [
        {"name": "Product 1", "price": 10.99, ...},
        {"name": "Product 2", "price": 20.99, ...}
    ]
    """
    try:
        result = pm.bulk_create(products)
        return {
            "success": True,
            "result": result,
            "message": f"Created {result['success_count']} products"
        }
    except Exception as e:
        logger.error(f"Bulk create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Results Management Endpoints

@firebase_router.post("/ai/results/save")
async def save_ai_result(request_data: Dict):
    """
    Save AI processing result to Firestore
    
    Request body:
    {
        "product": {"商品信息": "商品名称", "SKU": "sku123", "Product Code": "code123"},
        "result_type": "classify",  # or "describe"
        "result_data": {"category": "水果", "confidence": 0.95}
    }
    """
    try:
        product = request_data.get('product')
        result_type = request_data.get('result_type')
        result_data = request_data.get('result_data')
        
        if not all([product, result_type, result_data]):
            raise HTTPException(status_code=400, detail="Missing required fields: product, result_type, result_data")
        
        result = ai_manager.save_ai_result(product, result_type, result_data)
        if result:
            return {
                "success": True,
                "result": result,
                "message": f"Saved AI {result_type} result"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to save AI {result_type} result"
            }
    except Exception as e:
        logger.error(f"Save AI result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/ai/results")
async def get_ai_result(
    product: str = Query(..., description="Product information (JSON string)"),
    result_type: str = Query(..., description="Result type: classify or describe")
):
    """
    Get AI processing result for a product
    
    Query parameters:
    - product: Product information (JSON string)
    - result_type: "classify" or "describe"
    
    Returns:
    {
        "success": true,
        "result": {
            "id": "doc_id",
            "product_key": "product|sku|code",
            "result_type": "classify",
            "result": {"category": "水果", "confidence": 0.95},
            "created_at": "2026-03-11T...",
            "updated_at": "2026-03-11T..."
        }
    }
    """
    try:
        import json
        product_data = json.loads(product)
        result = ai_manager.get_ai_result(product_data, result_type)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Get AI result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/ai/results/all")
async def get_all_ai_results(
    result_type: Optional[str] = Query(None, description="Filter by result type: classify, describe"),
    limit: int = Query(100, description="Maximum number of results to return")
):
    """
    Get all AI results, optionally filtered by type
    
    Query parameters:
    - result_type: "classify", "describe", or None for all
    - limit: Maximum number of results (default: 100)
    
    Returns:
    {
        "success": true,
        "results": [...],
        "count": 50
    }
    """
    try:
        results = ai_manager.get_all_ai_results(result_type, limit)
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Get all AI results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.get("/ai/statistics")
async def get_ai_statistics():
    """
    Get statistics about AI processing results
    
    Returns:
    {
        "success": true,
        "statistics": {
            "total_results": 150,
            "classify_results": 80,
            "describe_results": 70,
            "unique_products": 45,
            "products_with_both": 35,
            "completion_rate": 77.8
        }
    }
    """
    try:
        stats = ai_manager.get_ai_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Get AI statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.delete("/ai/results")
async def delete_ai_result(
    product: str = Query(..., description="Product information (JSON string)"),
    result_type: str = Query(..., description="Result type: classify or describe")
):
    """
    Delete AI processing result for a product
    
    Query parameters:
    - product: Product information (JSON string)
    - result_type: "classify" or "describe"
    
    Returns:
    {
        "success": true,
        "message": "Deleted AI classify result"
    }
    """
    try:
        import json
        product_data = json.loads(product)
        success = ai_manager.delete_ai_result(product_data, result_type)
        return {
            "success": success,
            "message": f"{'Deleted' if success else 'Not found'} AI {result_type} result"
        }
    except Exception as e:
        logger.error(f"Delete AI result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@firebase_router.post("/ai/results/batch-get")
async def batch_get_ai_results(
    products: List[Dict],
    result_type: str
):
    """
    Batch get AI results for multiple products
    
    Request body:
    {
        "products": [
            {"商品信息": "商品1", "SKU": "sku1", "Product Code": "code1"},
            {"商品信息": "商品2", "SKU": "sku2", "Product Code": "code2"}
        ],
        "result_type": "classify"
    }
    
    Returns:
    {
        "success": true,
        "results": {
            "product1|sku1|code1": {...},
            "product2|sku2|code2": null
        }
    }
    """
    try:
        results = ai_manager.batch_get_ai_results(products, result_type)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.error(f"Batch get AI results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
