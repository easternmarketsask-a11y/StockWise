"""
Secure Configuration Manager using Google Cloud Secret Manager
"""
import os
import logging
from typing import Optional
try:
    from google.cloud import secretmanager
    from google.api_core import exceptions as gcp_exceptions
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

class SecureConfig:
    """Secure configuration manager using Secret Manager"""
    
    def __init__(self):
        self.client = None
        if SECRET_MANAGER_AVAILABLE:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Secret Manager client: {e}")
                self.client = None
        else:
            logger.warning("google-cloud-secret-manager not available, falling back to environment variables")
    
    def get_secret(self, secret_id: str, project_id: str = "stockwise-486801") -> Optional[str]:
        """Get secret from Secret Manager"""
        if not self.client:
            return self._get_env_fallback(secret_id)
        
        try:
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            secret_data = response.payload.data.decode("UTF-8")
            logger.info(f"Successfully retrieved secret: {secret_id}")
            return secret_data
        except gcp_exceptions.NotFound:
            logger.warning(f"Secret not found: {secret_id}")
            return self._get_env_fallback(secret_id)
        except gcp_exceptions.PermissionDenied:
            logger.error(f"Permission denied accessing secret: {secret_id}")
            return self._get_env_fallback(secret_id)
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            return self._get_env_fallback(secret_id)
    
    def _get_env_fallback(self, secret_id: str) -> Optional[str]:
        """Fallback to environment variables"""
        env_mapping = {
            "clover-api-key": "CLOVER_API_KEY",
            "merchant-id": "MERCHANT_ID", 
            "anthropic-api-key": "ANTHROPIC_API_KEY",
            "gemini-api-key": "GEMINI_API_KEY"
        }
        
        env_var = env_mapping.get(secret_id.lower())
        if env_var:
            value = os.environ.get(env_var)
            if value:
                logger.warning(f"Using environment variable fallback for {secret_id}")
                return value
        
        logger.error(f"No fallback available for secret: {secret_id}")
        return None

# Global instance
_secure_config = None

def get_secure_config() -> SecureConfig:
    """Get global secure config instance"""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfig()
    return _secure_config

def get_clover_api_key() -> str:
    """Get Clover API key securely"""
    config = get_secure_config()
    return config.get_secret("clover-api-key") or ""

def get_merchant_id() -> str:
    """Get Merchant ID securely"""
    config = get_secure_config()
    return config.get_secret("merchant-id") or ""

def get_anthropic_api_key() -> str:
    """Get Anthropic API key securely"""
    config = get_secure_config()
    return config.get_secret("anthropic-api-key") or ""

def get_gemini_api_key() -> str:
    """Get Gemini API key securely"""
    config = get_secure_config()
    return config.get_secret("gemini-api-key") or ""

def get_admin_token() -> str:
    """Get Admin Token securely"""
    config = get_secure_config()
    # Try secret manager first, then fall back to environment variable
    token = config.get_secret("admin-token")
    if not token:
        token = os.environ.get("ADMIN_TOKEN", "")
    return token
