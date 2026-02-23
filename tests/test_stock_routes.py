"""
股票API路由测试
"""

import unittest
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


class TestStockRoutes(unittest.TestCase):
    """股票API路由测试类"""

    def setUp(self):
        """测试前准备"""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        """测试后清理"""
        self.app_context.pop()

    def test_health_check(self):
        """测试健康检查接口"""
        response = self.client.get("/api/stocks/health")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["module"], "stock_data")
        self.assertIn("timestamp", data)

    def test_get_stock_info_invalid_code(self):
        """测试无效股票代码"""
        response = self.client.get("/api/stocks/info/abc")
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
        self.assertIn("股票代码格式错误", data["message"])

        response = self.client.get("/api/stocks/info/12345")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/api/stocks/info/1234567")
        self.assertEqual(response.status_code, 400)

    def test_get_fund_flow_invalid_parameters(self):
        """测试无效参数"""
        response = self.client.get("/api/stocks/flow/000001?days=0")
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")

        response = self.client.get("/api/stocks/flow/000001?days=31")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/api/stocks/top-fund-flow?limit=0")
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/api/stocks/top-fund-flow?limit=51")
        self.assertEqual(response.status_code, 400)

    def test_clear_cache(self):
        """测试清空缓存接口"""
        response = self.client.post("/api/stocks/cache/clear")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "缓存已清空")


if __name__ == "__main__":
    unittest.main()
