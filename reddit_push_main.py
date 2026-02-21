#!/usr/bin/env python3
"""
Reddit 每日推送 - 主入口脚本
"""

import sys
import argparse
from datetime import datetime
from reddit_daily_push import RedditDailyPusher

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Reddit 每日推送工具')
    parser.add_argument('--once', action='store_true', help='运行一次推送')
    parser.add_argument('--daemon', action='store_true', help='以守护进程运行')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--setup-cron', action='store_true', help='设置 cron 任务')
    
    args = parser.parse_args()
    
    # 创建推送器
    pusher = RedditDailyPusher()
    
    if args.once:
        # 单次运行
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始单次推送...")
        success = pusher.run_once()
        if success:
            print("✅ 推送成功")
        else:
            print("❌ 推送失败")
        sys.exit(0 if success else 1)
    
    elif args.daemon:
        # 守护进程模式
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动守护进程...")
        print(f"推送时间: {pusher.push_time}")
        print("按 Ctrl+C 停止")
        pusher.run_daily()
    
    elif args.test:
        # 测试模式
        print("🔧 测试模式")
        print("测试 Reddit 访问和消息构建...")
        
        # 测试获取内容
        from reddit_daily_push import RedditFetcher
        fetcher = RedditFetcher()
        
        print("\n1. 测试单个 subreddit 获取...")
        posts = fetcher.fetch_subreddit_rss('python', limit=3)
        print(f"   获取到 {len(posts)} 个帖子")
        for post in posts:
            print(f"   - {post.get('title', '无标题')[:50]}...")
        
        print("\n2. 测试多个 subreddit 获取...")
        results = fetcher.fetch_multiple_subreddits(['programming', 'technology'], limit_per_sub=2)
        for sub, sub_posts in results.items():
            print(f"   r/{sub}: {len(sub_posts)} 个帖子")
        
        print("\n3. 测试热门帖子获取...")
        trending = fetcher.get_trending_posts(['python', 'programming'], total_limit=5)
        print(f"   获取到 {len(trending)} 个热门帖子")
        
        print("\n✅ 测试完成")
    
    elif args.setup_cron:
        # 设置 cron 任务
        print("📅 设置 cron 定时任务...")
        from reddit_daily_push import setup_cron_job
        setup_cron_job()
    
    else:
        # 默认显示帮助
        parser.print_help()
        print("\n📋 使用示例:")
        print("  python reddit_push_main.py --once      # 立即运行一次")
        print("  python reddit_push_main.py --daemon    # 启动守护进程")
        print("  python reddit_push_main.py --test      # 测试模式")
        print("  python reddit_push_main.py --setup-cron # 设置 cron 任务")

if __name__ == '__main__':
    main()