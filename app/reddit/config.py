#!/usr/bin/env python3
"""
Reddit 推送配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# Reddit 配置
REDDIT_CONFIG = {
    # 代理设置
    'proxy_url': 'http://127.0.0.1:7890',  # Clash 代理地址
    
    # 关注的 subreddit 列表
    'subreddits': [
        'programming',      # 编程
        'technology',       # 技术
        'python',           # Python
        'webdev',           # 网页开发
        'linux',            # Linux
        'opensource',       # 开源
        'sysadmin',         # 系统管理
        'devops',           # DevOps
        'coding',           # 编码
        'learnprogramming', # 学习编程
    ],
    
    # 推送设置
    'push_time': '12:00',  # 每天推送时间 (24小时制)
    'max_posts_per_sub': 3,  # 每个 subreddit 最多获取帖子数
    'total_posts_limit': 15,  # 总帖子数量限制
    
    # 飞书配置
    'feishu': {
        'webhook_url': os.environ.get('FEISHU_WEBHOOK_URL', ''),
        'enabled': bool(os.environ.get('FEISHU_WEBHOOK_URL')),
    },
    
    # 日志配置
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': PROJECT_ROOT / 'reddit_push.log',
    },
    
    # 存储配置
    'storage': {
        'output_dir': PROJECT_ROOT / 'reddit_output',
        'records_dir': PROJECT_ROOT / 'reddit_records',
        'cache_dir': PROJECT_ROOT / 'reddit_cache',
    },
}

# 消息模板
MESSAGE_TEMPLATES = {
    'daily_title': "📰 Reddit 技术资讯日报 - {date}",
    'daily_content': """🚀 今日热门技术内容已送达！

**统计摘要:**
{stats}

**精选内容:** (共 {count} 条)
""",
    
    'weekly_title': "📊 Reddit 技术周报 - {date}",
    'weekly_content': """📈 本周技术热点汇总！

**本周最活跃社区:**
{top_subs}

**热门话题趋势:**
{trends}

**精选内容回顾:**
""",
}

# 关键词过滤（可选）
KEYWORDS = {
    'positive': [
        'tutorial', 'guide', 'how to', 'learn',
        'news', 'update', 'release', 'version',
        'tips', 'tricks', 'best practices',
        'open source', 'free', 'github',
    ],
    'negative': [
        'job', 'hire', 'career', 'salary',
        'political', 'controversial',
        'nsfw', 'spoiler',
    ]
}

def get_config():
    """获取配置"""
    return REDDIT_CONFIG

def get_message_templates():
    """获取消息模板"""
    return MESSAGE_TEMPLATES

def get_keywords():
    """获取关键词"""
    return KEYWORDS

def setup_directories():
    """创建必要的目录"""
    config = get_config()
    
    for dir_key in ['output_dir', 'records_dir', 'cache_dir']:
        dir_path = config['storage'][dir_key]
        dir_path.mkdir(exist_ok=True)
        print(f"创建目录: {dir_path}")

if __name__ == '__main__':
    setup_directories()
    print("Reddit 配置加载完成")