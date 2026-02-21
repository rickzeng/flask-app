"""
Pytest 配置和固件
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def flask_app():
    """Flask 应用固件"""
    from app import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(flask_app):
    """测试客户端固件"""
    return flask_app.test_client()


@pytest.fixture
def reddit_fetcher():
    """Reddit 内容获取器固件"""
    from reddit_daily_push import RedditContentFetcher
    return RedditContentFetcher(proxy_url="http://127.0.0.1:7890")


@pytest.fixture
def reddit_notifier():
    """Reddit 内容通知器固件"""
    from reddit_daily_push import RedditContentNotifier
    return RedditContentNotifier()


@pytest.fixture
def sample_reddit_content():
    """示例 Reddit 内容固件"""
    return [
        {
            'title': 'Python 3.12 新特性介绍',
            'link': 'https://reddit.com/r/python/comments/1',
            'source': 'python',
            'description': 'Python 3.12 引入了多项新特性和改进',
            'score': 150
        },
        {
            'title': 'Flask vs Django 比较',
            'link': 'https://reddit.com/r/webdev/comments/2',
            'source': 'webdev',
            'description': '比较 Flask 和 Django 框架的优缺点',
            'score': 80
        },
        {
            'title': 'Linux 内核 6.7 发布',
            'link': 'https://reddit.com/r/linux/comments/3',
            'source': 'linux',
            'description': 'Linux 内核 6.7 版本正式发布',
            'score': 200
        }
    ]