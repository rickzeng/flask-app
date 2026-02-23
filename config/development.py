"""
Development Configuration
"""

from .base import Config


class DevelopmentConfig(Config):
    """开发环境配置"""

    DEBUG = True
    LOG_LEVEL = "DEBUG"
    TESTING = False
