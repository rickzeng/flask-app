"""
V2free 浏览器自动化配置文件
存储登录凭据和浏览器配置
"""

import os

class V2freeConfig:
    """V2free 登录配置"""
    
    # V2free 登录凭据
    V2FREE_URL = 'https://w2.v2free.top/user'
    V2FREE_USERNAME = 'rickzeng@gmail.com'
    V2FREE_PASSWORD = 'pass@V2free'
    
    # 浏览器配置
    BROWSER_HEADLESS = True  # 无头模式
    BROWSER_TIMEOUT = 30000  # 30秒超时
    BROWSER_SLOW_MO = 100    # 操作延迟（毫秒）
    
    # 代理配置（通过 Clash）
    PROXY_SERVER = 'http://127.0.0.1:7890'
    USE_PROXY = True
    
    # 日志配置
    LOG_DIR = 'v2free_logs'
    LOG_FILE = os.path.join(LOG_DIR, 'v2free_access.log')
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 登录重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 秒
    
    # 截图配置
    SCREENSHOT_DIR = 'v2free_screenshots'
    SAVE_SCREENSHOT = True
    SCREENSHOT_ON_ERROR = True
