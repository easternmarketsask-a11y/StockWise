import requests
import logging
import os
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)

class CloverAPIHandler:
    def __init__(self):
        # Load .env file
        load_dotenv()

        # Support multiple env var formats
        self.api_key = str(os.environ.get("CLOVER_API_KEY", "")).strip()
        self.merchant_id = str(os.environ.get("MERCHANT_ID", "")).strip() or str(os.environ.get("CLOVER_MERCHANT_ID", "")).strip()

        # Validate config
        if not self.api_key or not self.merchant_id:
            logger.error("API config missing: CLOVER_API_KEY and MERCHANT_ID required")
            raise ValueError("API configuration missing. Set CLOVER_API_KEY and MERCHANT_ID environment variables.")

        self.base_url = f"https://api.clover.com/v3/merchants/{self.merchant_id}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def fetch_full_inventory(self):
        """Fetch full inventory"""
        items = []
        limit, offset = 1000, 0
        try:
            while True:
                url = f"{self.base_url}/items"
                res = requests.get(url, headers=self.headers, params={"limit": limit, "offset": offset}, timeout=15)

                if res.status_code != 200:
                    msg = f"Clover API error {res.status_code}: {res.text[:300]}"
                    logger.error(msg)
                    raise RuntimeError(msg)

                try:
                    data = res.json().get("elements", [])
                except UnicodeDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    # 尝试强制编码处理
                    try:
                        content = res.content.decode('utf-8', errors='replace')
                        import json
                        data = json.loads(content).get("elements", [])
                    except Exception as decode_error:
                        logger.error(f"Failed to decode response: {decode_error}")
                        return []
                for e in data:
                    items.append({
                        "id": e.get("id"),
                        "name": str(e.get("name") or ""),
                        "sku": str(e.get("sku") or ""),
                        "code": str(e.get("code") or ""),
                        "alt_code": str(e.get("alternateCode") or ""),
                        "price": e.get("price", 0) / 100
                    })
                if len(data) < limit:
                    break
                offset += limit
            logger.info(f"Fetched {len(items)} products from Clover API")
            return items
        except RuntimeError:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise RuntimeError(f"Network error connecting to Clover API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return []

    def fetch_targeted_sales(self, item_ids, start_ts, end_ts):
        """Fetch sales for specific items by ID"""
        all_data = []
        for item_id in item_ids:
            offset = 0
            while True:
                params = [
                    ('filter', f'item.id={item_id}'),
                    ('filter', f'createdTime>{start_ts}'),
                    ('filter', f'createdTime<{end_ts}'),
                    ('limit', '1000'),
                    ('offset', str(offset))
                ]
                try:
                    res = requests.get(f"{self.base_url}/line_items", headers=self.headers, params=params, timeout=20)
                    try:
                        data = res.json().get("elements", [])
                    except UnicodeDecodeError as e:
                        logger.error(f"JSON decode error in sales: {e}")
                        try:
                            content = res.content.decode('utf-8', errors='replace')
                            import json
                            data = json.loads(content).get("elements", [])
                        except Exception as decode_error:
                            logger.error(f"Failed to decode sales response: {decode_error}")
                            data = []
                    for record in data:
                        record['manual_id_link'] = item_id
                    all_data.extend(data)
                    if len(data) < 1000:
                        break
                    offset += 1000
                except Exception as e:
                    logger.warning(f"Error fetching sales for item {item_id}: {e}")
                    break
        logger.info(f"Fetched {len(all_data)} sales records")
        return all_data

    def fetch_full_period_sales(self, start_ts, end_ts):
        """Export: fetch all sales for a period"""
        all_data = []
        limit, offset = 1000, 0
        try:
            while True:
                params = [
                    ('filter', f'createdTime>{start_ts}'),
                    ('filter', f'createdTime<{end_ts}'),
                    ('expand', 'item'),
                    ('limit', '1000'),
                    ('offset', str(offset))
                ]
                res = requests.get(f"{self.base_url}/line_items", headers=self.headers, params=params, timeout=30)

                if res.status_code != 200:
                    msg = f"Clover API error {res.status_code}: {res.text[:300]}"
                    logger.error(msg)
                    raise RuntimeError(msg)

                try:
                    data = res.json().get("elements", [])
                except UnicodeDecodeError as e:
                    logger.error(f"JSON decode error in full period sales: {e}")
                    try:
                        content = res.content.decode('utf-8', errors='replace')
                        import json
                        data = json.loads(content).get("elements", [])
                    except Exception as decode_error:
                        logger.error(f"Failed to decode full period sales response: {decode_error}")
                        return []
                if not data:
                    break
                all_data.extend(data)
                logger.info(f"Synced {len(all_data)} sales records...")
                if len(data) < limit:
                    break
                offset += limit
            logger.info(f"Total sales records fetched: {len(all_data)}")
            return all_data
        except RuntimeError:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise RuntimeError(f"Network error connecting to Clover API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return []