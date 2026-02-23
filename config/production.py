"""
Production Configuration
"""

from .base import Config
import os


class ProductionConfig(Config):
    """生产环境配置"""

    DEBUG = False
    LOG_LEVEL = "WARNING"
    TESTING = False

    def __init__(self):
        """初始化生产环境配置"""
        super().__init__()
        self.SECRET_KEY = os.environ.get("SECRET_KEY")
        if not self.SECRET_KEY:
            raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
