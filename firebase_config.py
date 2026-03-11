"""
Firebase Configuration Module
Initializes Firebase Admin SDK for Firestore and Cloud Storage
"""
import os
import json
import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, storage

logger = logging.getLogger(__name__)

class FirebaseConfig:
    """Firebase configuration and initialization"""
    
    _app = None
    _db = None
    _bucket = None
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if cls._app is not None:
            logger.info("Firebase already initialized")
            return
        
        try:
            # Method 1: Use service account key file
            service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                logger.info(f"Using service account from file: {service_account_path}")
            
            # Method 2: Use service account JSON from environment variable
            elif os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"):
                service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
                service_account_dict = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_dict)
                logger.info("Using service account from environment variable")
            
            # Method 3: Use default credentials (for Cloud Run)
            else:
                cred = credentials.ApplicationDefault()
                logger.info("Using application default credentials")
            
            # Get storage bucket name
            storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET", "stockwise-486801.appspot.com")
            
            # Initialize Firebase app
            cls._app = firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })
            
            # Initialize Firestore
            cls._db = firestore.client()
            
            # Initialize Cloud Storage
            cls._bucket = storage.bucket()
            
            logger.info("Firebase initialized successfully")
            logger.info(f"Storage bucket: {storage_bucket}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    @classmethod
    def get_db(cls) -> firestore.Client:
        """Get Firestore client"""
        if cls._db is None:
            cls.initialize()
        return cls._db
    
    @classmethod
    def get_bucket(cls):
        """Get Cloud Storage bucket"""
        if cls._bucket is None:
            cls.initialize()
        return cls._bucket
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Firebase is initialized"""
        return cls._app is not None


def get_firestore_client() -> firestore.Client:
    """Get Firestore client instance"""
    return FirebaseConfig.get_db()


def get_storage_bucket():
    """Get Cloud Storage bucket instance"""
    return FirebaseConfig.get_bucket()
