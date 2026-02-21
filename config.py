"""
Flask 应用程序配置文件
"""

import os

class Config:
    """基础配置类"""
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # 应用程序配置
    APP_NAME = 'Flask 应用程序'
    APP_VERSION = '1.0.0'
    
    # API 配置
    API_PREFIX = '/api'
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 股票数据配置
    STOCK_CACHE_TIMEOUT = int(os.environ.get('STOCK_CACHE_TIMEOUT', 300))  # 5分钟
    STOCK_API_TIMEOUT = int(os.environ.get('STOCK_API_TIMEOUT', 10))  # 10秒

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    def __init__(self):
        """初始化生产环境配置"""
        super().__init__()
        # 生产环境应该设置安全的密钥
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        if not self.SECRET_KEY:
            raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """
    获取配置对象
    
    Args:
        config_name: 配置名称（development/production/testing）
    
    Returns:
        配置类实例
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config.get(config_name)
    if config_class is None:
        config_class = config['default']
    
    return config_class()