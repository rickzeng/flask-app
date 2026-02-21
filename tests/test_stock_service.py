"""
股票数据服务单元测试
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from app.stock_service import StockDataProvider


class TestStockDataProvider(unittest.TestCase):
    """股票数据提供者测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.provider = StockDataProvider()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.provider.base_url)
        self.assertEqual(self.provider.cache, {})
        self.assertEqual(self.provider.cache_expire_time, {})
        self.assertEqual(self.provider.default_cache_timeout, 300)
    
    def test_cache_validation(self):
        """测试缓存验证"""
        # 测试不存在的key
        self.assertFalse(self.provider._is_cache_valid("non_existent_key"))
        
        # 测试存在的key但没有过期时间
        self.provider.cache["test_key"] = {"data": "test"}
        self.assertFalse(self.provider._is_cache_valid("test_key"))
        
        # 测试有效的缓存
        import time
        self.provider.cache_expire_time["test_key"] = time.time() + 60
        self.assertTrue(self.provider._is_cache_valid("test_key"))
        
        # 测试过期的缓存
        self.provider.cache_expire_time["test_key"] = time.time() - 60
        self.assertFalse(self.provider._is_cache_valid("test_key"))
    
    def test_cache_operations(self):
        """测试缓存操作"""
        # 测试设置和获取缓存
        test_data = {"code": "000001", "name": "平安银行"}
        self.provider._set_cache("test_stock", test_data)
        
        cached_data = self.provider._get_from_cache("test_stock")
        self.assertEqual(cached_data, test_data)
        
        # 测试清空缓存
        self.provider.clear_cache()
        self.assertEqual(self.provider.cache, {})
        self.assertEqual(self.provider.cache_expire_time, {})
    
    @patch('app.stock_service.requests.get')
    def test_get_stock_basic_info(self, mock_get):
        """测试获取股票基本信息"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "f2": 1050,  # 价格10.50
                "f3": 20,    # 涨跌0.20
                "f170": 194,  # 涨跌幅1.94%
                "f5": 1000000,  # 成交量
                "f6": 10500000,  # 成交额
                "f58": "平安银行"  # 股票名称
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 测试成功获取
        result = self.provider.get_stock_basic_info("000001")
        self.assertEqual(result["code"], "000001")
        self.assertEqual(result["name"], "平安银行")
        self.assertEqual(result["price"], 10.50)
        self.assertEqual(result["change"], 0.20)
        self.assertEqual(result["change_percent"], 1.94)
        
        # 验证缓存生效
        mock_get.reset_mock()
        result = self.provider.get_stock_basic_info("000001")
        self.assertEqual(result["name"], "平安银行")
        mock_get.assert_not_called()
    
    @patch('app.stock_service.requests.get')
    def test_get_stock_fund_flow(self, mock_get):
        """测试获取股票资金流向"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "klines": [
                    "2024-02-19,10000,5000,3000,2000,-500,-15000",
                    "2024-02-20,15000,8000,4000,3000,500,-10000"
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 测试成功获取
        result = self.provider.get_stock_fund_flow("000001", 2)
        self.assertEqual(result["code"], "000001")
        self.assertEqual(len(result["fund_flows"]), 2)
        self.assertEqual(result["fund_flows"][0]["main_flow"], 1.0)
        self.assertEqual(result["fund_flows"][1]["main_flow"], 1.5)
    
    @patch('app.stock_service.requests.get')
    def test_get_top_fund_flow_stocks(self, mock_get):
        """测试获取资金流入前N股票"""
        # 模拟股票列表API响应
        def mock_get_side_effect(url, params=None, timeout=None):
            mock_response = MagicMock()
            
            if 'clist' in url:
                # 返回股票列表
                mock_response.json.return_value = {
                    "data": {
                        "diff": [
                            {
                                "f12": "000001",  # 股票代码
                                "f14": "平安银行",  # 股票名称
                                "f2": 1050,  # 价格
                                "f3": 20,    # 涨跌
                                "f170": 194  # 涨跌幅
                            },
                            {
                                "f12": "000002",
                                "f14": "万科A",
                                "f2": 850,
                                "f3": -10,
                                "f170": -117
                            }
                        ]
                    }
                }
            else:
                # 返回空资金流向
                mock_response.json.return_value = {
                    "data": {
                        "klines": [
                            "2024-02-19,10000,5000,3000,2000,-500,-15000"
                        ]
                    }
                }
            
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # 测试成功获取
        result = self.provider.get_top_fund_flow_stocks(5, 10)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()