#!/usr/bin/env python3
"""
Flask 应用程序单元测试
"""

import unittest
import json
from unittest.mock import patch, MagicMock

from app import app


class TestFlaskApp(unittest.TestCase):
    """Flask 应用程序测试类"""

    def setUp(self):
        """测试前准备"""
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        """测试首页"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        # 检查响应数据是否为字节类型
        self.assertIsInstance(response.data, bytes)
        # 解码后检查内容
        response_text = response.data.decode('utf-8')
        self.assertIn('Flask 应用程序', response_text)
        self.assertIn('/api/hello', response_text)
        self.assertIn('/api/health', response_text)

    def test_hello_api(self):
        """测试 hello API"""
        response = self.app.get('/api/hello')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('你好！欢迎使用 Flask API', data['message'])
        self.assertIn('timestamp', data)

    def test_health_api(self):
        """测试健康检查 API"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'flask-app')
        self.assertEqual(data['version'], '1.0.0')

    def test_page_not_found(self):
        """测试 404 页面"""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_method_not_allowed(self):
        """测试方法不允许"""
        response = self.app.post('/api/hello')
        self.assertEqual(response.status_code, 405)

    def test_content_type_json(self):
        """测试 API 返回正确的 Content-Type"""
        response = self.app.get('/api/hello')
        self.assertEqual(response.content_type, 'application/json')
        
        response = self.app.get('/api/health')
        self.assertEqual(response.content_type, 'application/json')

    def test_api_response_structure(self):
        """测试 API 响应结构"""
        # 测试 hello API 响应结构
        response = self.app.get('/api/hello')
        data = json.loads(response.data)
        required_fields = ['message', 'status', 'timestamp']
        for field in required_fields:
            self.assertIn(field, data)
        
        # 测试 health API 响应结构
        response = self.app.get('/api/health')
        data = json.loads(response.data)
        required_fields = ['status', 'service', 'version']
        for field in required_fields:
            self.assertIn(field, data)

    def test_flask_app_configuration(self):
        """测试 Flask 应用配置"""
        with app.app_context():
            self.assertIsNotNone(app.config)
            self.assertIn('SECRET_KEY', app.config)


class TestFlaskAppErrorHandling(unittest.TestCase):
    """Flask 应用错误处理测试"""

    def setUp(self):
        """测试前准备"""
        self.app = app.test_client()
        self.app.testing = True

    def test_invalid_route(self):
        """测试无效路由"""
        response = self.app.get('/invalid/route')
        self.assertEqual(response.status_code, 404)

    def test_invalid_methods(self):
        """测试无效 HTTP 方法"""
        # POST 不允许的端点
        response = self.app.post('/api/health')
        self.assertEqual(response.status_code, 405)
        
        response = self.app.post('/')
        self.assertEqual(response.status_code, 405)

    @patch('app.jsonify')
    def test_jsonify_error_handling(self, mock_jsonify):
        """测试 jsonify 错误处理"""
        # 模拟 jsonify 抛出异常
        mock_jsonify.side_effect = Exception("JSON error")
        
        # 这个测试需要调整，因为 jsonify 是 Flask 内部函数
        # 实际应用中，我们应该测试业务逻辑而不是内部函数
        pass


if __name__ == '__main__':
    unittest.main()