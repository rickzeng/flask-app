"""
Testing Configuration
"""

from .base import Config


class TestingConfig(Config):
    """测试环境配置"""

    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"
