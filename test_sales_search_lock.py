#!/usr/bin/env python3
"""Regression tests to lock sales-search behavior."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

import app_server


class _FakeAPI:
    def __init__(self, inventory, raw_sales):
        self.inventory = inventory
        self.raw_sales = raw_sales
        self.calls = []
        self.last_targeted_args = None

    def fetch_full_inventory(self):
        self.calls.append("fetch_full_inventory")
        return self.inventory

    def fetch_targeted_sales(self, item_ids, start_ts, end_ts):
        self.calls.append("fetch_targeted_sales")
        self.last_targeted_args = (item_ids, start_ts, end_ts)
        return self.raw_sales


class SalesSearchLockTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app_server.app)

    def test_empty_inventory_returns_404(self):
        fake_api = _FakeAPI([], [])

        with patch.object(app_server, "get_api_handler", return_value=fake_api):
            response = self.client.get(
                "/api/sales/search",
                params={"query": "milk", "start_date": "2026-03-01", "end_date": "2026-03-08"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "No products found")

    def test_no_matching_products_returns_404(self):
        inventory = [{"id": "p1", "name": "Orange", "sku": "O-1", "code": "100", "alt_code": ""}]
        fake_api = _FakeAPI(inventory, [])

        with patch.object(app_server, "get_api_handler", return_value=fake_api):
            response = self.client.get(
                "/api/sales/search",
                params={"query": "milk", "start_date": "2026-03-01", "end_date": "2026-03-08"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "No matching products found")

    def test_search_uses_full_inventory_then_targeted_sales(self):
        inventory = [{"id": "p1", "name": "Milk", "sku": "M-1", "code": "200", "alt_code": "A-200", "price": 3.5}]
        raw_sales = [{"manual_id_link": "p1", "price": 350, "unitQty": 1000}]
        fake_api = _FakeAPI(inventory, raw_sales)

        result_df = pd.DataFrame(
            [
                {
                    "商品信息": "Milk",
                    "售价": "$3.50",
                    "区间销量": 1.0,
                    "销售总额": "$3.50",
                    "Product Code": "200",
                    "SKU": "M-1",
                }
            ]
        )

        with patch.object(app_server, "get_api_handler", return_value=fake_api), patch.object(
            app_server.data_engine, "audit_process", return_value=result_df
        ):
            response = self.client.get(
                "/api/sales/search",
                params={"query": "milk", "start_date": "2026-03-01", "end_date": "2026-03-08"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake_api.calls, ["fetch_full_inventory", "fetch_targeted_sales"])

        item_ids, start_ts, end_ts = fake_api.last_targeted_args
        self.assertEqual(item_ids, ["p1"])

        expected_start = int(datetime.strptime("2026-03-01", "%Y-%m-%d").timestamp() * 1000)
        expected_end = int((datetime.strptime("2026-03-08", "%Y-%m-%d") + timedelta(days=1)).timestamp() * 1000) - 1
        self.assertEqual(start_ts, expected_start)
        self.assertEqual(end_ts, expected_end)

        body = response.json()
        self.assertEqual(body.get("matched_products"), 1)
        self.assertEqual(body.get("sales_records"), 1)


if __name__ == "__main__":
    unittest.main()
