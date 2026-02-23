#!/usr/bin/env python3
"""
配置模块测试
"""

import unittest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.base import Config


class TestConfig(unittest.TestCase):
    """配置模块测试"""

    def test_config_attributes(self):
        """测试配置属性"""
        config = Config()

        # 测试基本属性
        self.assertTrue(hasattr(config, "SECRET_KEY"))
        self.assertTrue(hasattr(config, "DEBUG"))

        # 测试类型
        self.assertIsInstance(config.SECRET_KEY, str)
        self.assertIsInstance(config.DEBUG, bool)

        # 测试默认值
        self.assertEqual(config.DEBUG, True)
        self.assertEqual(config.SECRET_KEY, "dev-secret-key-change-in-production")

    def test_config_environment_override(self):
        """测试环境变量覆盖"""
        import os

        # 保存原始环境变量
        original_debug = os.environ.get("FLASK_DEBUG")
        original_secret = os.environ.get("FLASK_SECRET_KEY")

        try:
            # 设置环境变量
            os.environ["FLASK_DEBUG"] = "False"
            os.environ["FLASK_SECRET_KEY"] = "test-secret-key"

            # 重新导入配置以应用环境变量
            import importlib
            import config

            importlib.reload(config)

            config_obj = config.Config()

            # 测试环境变量是否生效
            self.assertEqual(config_obj.DEBUG, False)
            self.assertEqual(config_obj.SECRET_KEY, "test-secret-key")

        finally:
            # 恢复环境变量
            if original_debug is not None:
                os.environ["FLASK_DEBUG"] = original_debug
            else:
                os.environ.pop("FLASK_DEBUG", None)

            if original_secret is not None:
                os.environ["FLASK_SECRET_KEY"] = original_secret
            else:
                os.environ.pop("FLASK_SECRET_KEY", None)

            # 重新加载原始配置
            import importlib
            import config

            importlib.reload(config)

    def test_config_methods(self):
        """测试配置方法"""
        config = Config()

        # 测试 to_dict 方法
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("SECRET_KEY", config_dict)
        self.assertIn("DEBUG", config_dict)

        # 测试 __repr__ 方法
        repr_str = repr(config)
        self.assertIsInstance(repr_str, str)
        self.assertIn("Config", repr_str)

        # 测试 __str__ 方法
        str_str = str(config)
        self.assertIsInstance(str_str, str)
        self.assertIn("Config", str_str)

    def test_config_validation(self):
        """测试配置验证"""
        config = Config()

        # 测试 SECRET_KEY 长度
        self.assertGreaterEqual(len(config.SECRET_KEY), 8)

        # 测试 DEBUG 类型
        self.assertIn(config.DEBUG, [True, False])


if __name__ == "__main__":
    unittest.main()
