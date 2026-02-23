"""
Config Package
"""

from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name=None):
    """
    获取配置对象

    Args:
        config_name: 配置名称（development/production/testing）

    Returns:
        配置类实例
    """
    import os

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = config.get(config_name)
    if config_class is None:
        config_class = config["default"]

    return config_class()


__all__ = [
    "Config",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
    "get_config",
    "config",
]
