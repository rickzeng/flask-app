#!/usr/bin/env python3
"""
Reddit 每日推送脚本
每天中午12点获取指定 subreddit 内容并通过 Feishu 推送
"""

import os
import sys
import json
import time
import schedule
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from pathlib import Path

# 添加项目目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'reddit_push.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RedditFetcher:
    """Reddit 内容获取器"""
    
    def __init__(self, proxy_url: str = "http://127.0.0.1:7890"):
        """
        初始化 Reddit 获取器
        
        Args:
            proxy_url: Clash 代理地址
        """
        self.proxy_url = proxy_url
        self.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # 默认关注的 subreddit
        self.default_subreddits = [
            'programming',
            'technology',
            'python',
            'webdev',
            'linux',
            'opensource'
        ]
        
        logger.info(f"RedditFetcher 初始化完成，使用代理: {proxy_url}")
    
    def fetch_subreddit_rss(self, subreddit: str, limit: int = 10) -> List[Dict]:
        """
        获取 subreddit 的 RSS 内容
        
        Args:
            subreddit: subreddit 名称
            limit: 最大帖子数量
            
        Returns:
            帖子列表
        """
        url = f"https://www.reddit.com/r/{subreddit}/.rss"
        
        try:
            logger.info(f"获取 subreddit: r/{subreddit}")
            response = requests.get(
                url,
                proxies=self.proxies,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                return self.parse_rss_content(response.text, subreddit, limit)
            else:
                logger.error(f"获取失败: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"获取 subreddit r/{subreddit} 时出错: {e}")
            return []
    
    def parse_rss_content(self, xml_content: str, subreddit: str, limit: int) -> List[Dict]:
        """
        解析 RSS XML 内容
        
        Args:
            xml_content: RSS XML 内容
            subreddit: subreddit 名称
            limit: 最大帖子数量
            
        Returns:
            解析后的帖子列表
        """
        try:
            # 解析 XML
            root = ET.fromstring(xml_content)
            
            # Reddit RSS 使用 Atom 格式，查找所有 entry 元素
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # 尝试不同的元素查找方式
            items = []
            
            # 方法1: 查找 Atom entry 元素
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            # 方法2: 如果没有找到，尝试其他命名空间
            if not items:
                items = root.findall('.//entry')
            
            # 方法3: 尝试 item 元素（传统 RSS）
            if not items:
                items = root.findall('.//item')
            
            posts = []
            for item in items[:limit]:
                # 提取标题
                title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                if title_elem is None:
                    title_elem = item.find('title')
                
                # 提取链接
                link_elem = item.find('{http://www.w3.org/2005/Atom}link')
                if link_elem is None:
                    link_elem = item.find('link')
                
                # 提取作者
                author_elem = item.find('{http://www.w3.org/2005/Atom}author')
                if author_elem is not None:
                    name_elem = author_elem.find('{http://www.w3.org/2005/Atom}name')
                    author = name_elem.text if name_elem is not None else ''
                else:
                    author_elem = item.find('author')
                    author = author_elem.text if author_elem is not None else ''
                
                # 提取发布时间
                published_elem = item.find('{http://www.w3.org/2005/Atom}published')
                if published_elem is None:
                    published_elem = item.find('pubDate')
                
                # 提取内容
                content_elem = item.find('{http://www.w3.org/2005/Atom}content')
                if content_elem is None:
                    content_elem = item.find('description')
                
                post = {
                    'subreddit': subreddit,
                    'title': title_elem.text if title_elem is not None else '无标题',
                    'link': link_elem.get('href') if link_elem is not None and 'href' in link_elem.attrib else (link_elem.text if link_elem is not None else ''),
                    'description': content_elem.text if content_elem is not None else '',
                    'author': author,
                    'pub_date': published_elem.text if published_elem is not None else '',
                    'guid': '',
                    'fetched_at': datetime.now().isoformat()
                }
                
                # 清理描述文本
                if post['description']:
                    # 移除 HTML 标签
                    import re
                    post['description'] = re.sub(r'<[^>]+>', '', post['description'])
                    post['description'] = post['description'][:200] + '...' if len(post['description']) > 200 else post['description']
                
                # 如果链接为空，尝试从其他属性获取
                if not post['link'] and link_elem is not None:
                    # 尝试获取 href 属性
                    post['link'] = link_elem.get('href', '')
                
                posts.append(post)
            
            logger.info(f"解析到 {len(posts)} 个帖子来自 r/{subreddit}")
            return posts
            
        except Exception as e:
            logger.error(f"解析 RSS 内容时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _get_element_text(self, element, tag_name: str) -> str:
        """安全获取元素文本"""
        try:
            elem = element.find(tag_name)
            if elem is not None:
                return elem.text or ''
        except:
            pass
        return ''
    
    def fetch_multiple_subreddits(self, subreddits: List[str], limit_per_sub: int = 5) -> Dict[str, List[Dict]]:
        """
        获取多个 subreddit 的内容
        
        Args:
            subreddits: subreddit 名称列表
            limit_per_sub: 每个 subreddit 的最大帖子数
            
        Returns:
            按 subreddit 分组的帖子字典
        """
        results = {}
        
        for subreddit in subreddits:
            posts = self.fetch_subreddit_rss(subreddit, limit_per_sub)
            if posts:
                results[subreddit] = posts
            time.sleep(1)  # 避免请求过快
        
        return results
    
    def get_trending_posts(self, subreddits: Optional[List[str]] = None, 
                          total_limit: int = 15) -> List[Dict]:
        """
        获取热门帖子（按时间排序）
        
        Args:
            subreddits: 要获取的 subreddit 列表，None 则使用默认
            total_limit: 总帖子数量限制
            
        Returns:
            合并后的热门帖子列表
        """
        if subreddits is None:
            subreddits = self.default_subreddits
        
        all_posts = []
        results = self.fetch_multiple_subreddits(subreddits, limit_per_sub=3)
        
        for subreddit, posts in results.items():
            for post in posts:
                post['score'] = self._calculate_post_score(post)
                all_posts.append(post)
        
        # 按分数排序
        all_posts.sort(key=lambda x: x['score'], reverse=True)
        
        return all_posts[:total_limit]
    
    def _calculate_post_score(self, post: Dict) -> int:
        """计算帖子分数（简单实现）"""
        score = 0
        
        # 标题长度适中加分
        title_len = len(post.get('title', ''))
        if 20 <= title_len <= 100:
            score += 10
        
        # 描述长度加分
        desc_len = len(post.get('description', ''))
        if desc_len > 50:
            score += 5
        
        # 特定关键词加分
        keywords = ['python', 'tutorial', 'guide', 'news', 'update', 'release']
        title = post.get('title', '').lower()
        for keyword in keywords:
            if keyword in title:
                score += 3
        
        return score

class FeishuNotifier:
    """飞书消息通知器"""
    
    def __init__(self):
        """初始化飞书通知器"""
        # 这里需要配置飞书的 webhook 或 API
        # 暂时使用模拟发送，实际使用时需要配置真实 webhook
        self.webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
        self.enabled = bool(self.webhook_url)
        
        if self.enabled:
            logger.info("飞书通知器已启用")
        else:
            logger.warning("飞书通知器未配置，将使用模拟发送")
    
    def send_message(self, title: str, content: str, posts: List[Dict] = None) -> bool:
        """
        发送消息到飞书
        
        Args:
            title: 消息标题
            content: 消息内容
            posts: 帖子列表（可选）
            
        Returns:
            是否发送成功
        """
        try:
            if self.enabled:
                return self._send_real_message(title, content, posts)
            else:
                return self._send_mock_message(title, content, posts)
                
        except Exception as e:
            logger.error(f"发送飞书消息时出错: {e}")
            return False
    
    def _send_real_message(self, title: str, content: str, posts: List[Dict]) -> bool:
        """发送真实飞书消息"""
        # 构建飞书消息卡片
        message_card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": []
            }
        }
        
        # 添加内容
        message_card["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        })
        
        # 添加帖子列表
        if posts:
            for i, post in enumerate(posts[:5], 1):  # 只显示前5个
                post_element = {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"{i}. **{post.get('title', '无标题')}**\n"
                                  f"   📍 r/{post.get('subreddit', 'unknown')}\n"
                                  f"   🔗 [查看原文]({post.get('link', '#')})"
                    },
                    "fields": []
                }
                message_card["card"]["elements"].append(post_element)
        
        # 添加时间戳
        message_card["card"]["elements"].append({
            "tag": "note",
            "elements": [{
                "tag": "plain_text",
                "content": f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }]
        })
        
        # 发送请求
        try:
            response = requests.post(
                self.webhook_url,
                json=message_card,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("飞书消息发送成功")
                return True
            else:
                logger.error(f"飞书消息发送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送飞书请求时出错: {e}")
            return False
    
    def _send_mock_message(self, title: str, content: str, posts: List[Dict]) -> bool:
        """模拟发送消息（用于测试）"""
        logger.info("=" * 60)
        logger.info(f"📨 模拟发送飞书消息")
        logger.info(f"标题: {title}")
        logger.info(f"内容: {content}")
        
        if posts:
            logger.info("热门帖子:")
            for i, post in enumerate(posts[:5], 1):
                logger.info(f"  {i}. {post.get('title', '无标题')}")
                logger.info(f"     来源: r/{post.get('subreddit', 'unknown')}")
                logger.info(f"     链接: {post.get('link', '#')}")
        
        logger.info("=" * 60)
        
        # 同时保存到文件
        self._save_to_file(title, content, posts)
        
        return True
    
    def _save_to_file(self, title: str, content: str, posts: List[Dict]):
        """保存消息到文件"""
        try:
            output_dir = project_root / 'reddit_output'
            output_dir.mkdir(exist_ok=True)
            
            filename = output_dir / f"reddit_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"标题: {title}\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"内容: {content}\n\n")
                
                if posts:
                    f.write("热门帖子:\n")
                    for i, post in enumerate(posts, 1):
                        f.write(f"\n{i}. {post.get('title', '无标题')}\n")
                        f.write(f"   来源: r/{post.get('subreddit', 'unknown')}\n")
                        f.write(f"   链接: {post.get('link', '#')}\n")
                        if post.get('description'):
                            f.write(f"   描述: {post.get('description')}\n")
            
            logger.info(f"消息已保存到文件: {filename}")
            
        except Exception as e:
            logger.error(f"保存到文件时出错: {e}")

class RedditDailyPusher:
    """Reddit 每日推送主类"""
    
    def __init__(self):
        """初始化推送器"""
        self.reddit_fetcher = RedditFetcher()
        self.feishu_notifier = FeishuNotifier()
        
        # 配置
        self.subreddits = [
            'programming',
            'technology', 
            'python',
            'webdev',
            'linux',
            'opensource'
        ]
        
        self.push_time = "12:00"  # 每天中午12点推送
        
        logger.info(f"RedditDailyPusher 初始化完成，推送时间: {self.push_time}")
    
    def fetch_and_push(self):
        """获取并推送内容"""
        try:
            logger.info("开始获取 Reddit 内容...")
            
            # 获取热门帖子
            trending_posts = self.reddit_fetcher.get_trending_posts(
                self.subreddits,
                total_limit=10
            )
            
            if not trending_posts:
                logger.warning("未获取到任何帖子内容")
                return False
            
            # 构建消息内容
            title = f"📰 Reddit 技术资讯日报 - {datetime.now().strftime('%Y-%m-%d')}"
            
            subreddit_counts = {}
            for post in trending_posts:
                sub = post.get('subreddit', 'unknown')
                subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
            
            stats_text = " | ".join([f"r/{sub}: {count}" for sub, count in subreddit_counts.items()])
            
            content = f"""🚀 今日热门技术内容已送达！

**统计摘要:**
{stats_text}

**精选内容:** (共 {len(trending_posts)} 条)
"""
            
            # 发送消息
            success = self.feishu_notifier.send_message(title, content, trending_posts)
            
            if success:
                logger.info("Reddit 内容推送成功")
                # 保存推送记录
                self._save_push_record(trending_posts)
            else:
                logger.error("Reddit 内容推送失败")
            
            return success
            
        except Exception as e:
            logger.error(f"获取并推送内容时出错: {e}")
            return False
    
    def _save_push_record(self, posts: List[Dict]):
        """保存推送记录"""
        try:
            record = {
                'push_time': datetime.now().isoformat(),
                'post_count': len(posts),
                'subreddits': list(set(p['subreddit'] for p in posts)),
                'posts': posts
            }
            
            records_dir = project_root / 'reddit_records'
            records_dir.mkdir(exist_ok=True)
            
            filename = records_dir / f"push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            logger.info(f"推送记录已保存: {filename}")
            
        except Exception as e:
            logger.error(f"保存推送记录时出错: {e}")
    
    def run_daily(self):
        """运行每日推送任务"""
        logger.info(f"启动每日推送服务，推送时间: {self.push_time}")
        
        # 安排每日任务
        schedule.every().day.at(self.push_time).do(self.fetch_and_push)
        
        # 立即运行一次（测试用）
        logger.info("立即运行一次测试推送...")
        self.fetch_and_push()
        
        # 保持运行
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止服务")
                break
            except Exception as e:
                logger.error(f"调度器运行时出错: {e}")
                time.sleep(300)  # 出错后等待5分钟
    
    def run_once(self):
        """运行一次（手动触发）"""
        logger.info("手动触发单次推送...")
        return self.fetch_and_push()

def setup_cron_job():
    """设置 cron 定时任务"""
    cron_content = f"""# Reddit 每日推送任务
# 每天中午12点运行
0 12 * * * cd {project_root} && {sys.executable} {__file__} --once >> {project_root}/reddit_cron.log 2>&1

# 测试任务（每5分钟运行一次）
# */5 * * * * cd {project_root} && {sys.executable} {__file__} --once >> {project_root}/reddit_test.log 2>&1
"""
    
    cron_file = project_root / 'reddit_cron.txt'
    with open(cron_file, 'w') as f:
        f.write(cron_content)
    
    logger.info(f"Cron 配置已保存到: {cron_file}")
    logger.info("请手动添加到 crontab: crontab -e")
    
    # 返回安装说明
    install_guide = f"""
    📅 Cron 任务安装说明:
    1. 编辑 crontab: crontab -e
    2. 添加以下行:
    
    {cron_content}
    
    3. 保存并退出
    4. 验证: crontab -l
    """
    
    return install_guide