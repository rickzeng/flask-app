#!/usr/bin/env python3
"""
Reddit 推送功能测试
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from reddit_daily_push import RedditFetcher, FeishuNotifier, RedditDailyPusher


class TestRedditFetcher(unittest.TestCase):
    """Reddit 获取器测试类"""

    def setUp(self):
        """测试前准备"""
        self.fetcher = RedditFetcher(proxy_url="http://test-proxy:8080")
        self.test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Subreddit</title>
            <entry>
                <title>Test Post 1</title>
                <link href="https://reddit.com/test1" />
                <author>
                    <name>testuser1</name>
                </author>
                <published>2023-01-01T12:00:00Z</published>
                <content type="html">Test content 1 with some description</content>
            </entry>
            <entry>
                <title>Test Post 2</title>
                <link href="https://reddit.com/test2" />
                <author>
                    <name>testuser2</name>
                </author>
                <published>2023-01-01T13:00:00Z</published>
                <content type="html">Test content 2 with more description</content>
            </entry>
        </feed>'''

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.fetcher.proxy_url, "http://test-proxy:8080")
        self.assertEqual(self.fetcher.proxies['http'], "http://test-proxy:8080")
        self.assertEqual(self.fetcher.proxies['https'], "http://test-proxy:8080")
        self.assertIn('User-Agent', self.fetcher.headers)

    @patch('reddit_daily_push.requests.get')
    def test_fetch_subreddit_rss_success(self, mock_get):
        """测试成功获取 subreddit RSS"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.test_xml_content
        mock_get.return_value = mock_response

        # 测试获取
        posts = self.fetcher.fetch_subreddit_rss('test', limit=5)
        
        # 验证结果
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]['title'], 'Test Post 1')
        self.assertEqual(posts[0]['subreddit'], 'test')
        self.assertEqual(posts[0]['link'], 'https://reddit.com/test1')
        self.assertEqual(posts[0]['author'], 'testuser1')
        
        # 验证请求参数
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('proxies', call_args.kwargs)
        self.assertIn('headers', call_args.kwargs)
        self.assertIn('timeout', call_args.kwargs)

    @patch('reddit_daily_push.requests.get')
    def test_fetch_subreddit_rss_failure(self, mock_get):
        """测试获取 subreddit RSS 失败"""
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # 测试获取
        posts = self.fetcher.fetch_subreddit_rss('nonexistent', limit=5)
        
        # 验证结果
        self.assertEqual(len(posts), 0)

    @patch('reddit_daily_push.requests.get')
    def test_fetch_subreddit_rss_exception(self, mock_get):
        """测试获取 subreddit RSS 异常"""
        # 模拟异常
        mock_get.side_effect = Exception("Network error")

        # 测试获取
        posts = self.fetcher.fetch_subreddit_rss('test', limit=5)
        
        # 验证结果
        self.assertEqual(len(posts), 0)

    def test_parse_rss_content(self):
        """测试解析 RSS 内容"""
        posts = self.fetcher.parse_rss_content(self.test_xml_content, 'test', 5)
        
        # 验证解析结果
        self.assertEqual(len(posts), 2)
        
        # 验证第一个帖子
        self.assertEqual(posts[0]['title'], 'Test Post 1')
        self.assertEqual(posts[0]['subreddit'], 'test')
        self.assertEqual(posts[0]['link'], 'https://reddit.com/test1')
        self.assertEqual(posts[0]['author'], 'testuser1')
        self.assertEqual(posts[0]['pub_date'], '2023-01-01T12:00:00Z')
        self.assertIn('Test content 1', posts[0]['description'])
        self.assertIn('fetched_at', posts[0])

    def test_parse_rss_content_with_traditional_format(self):
        """测试解析传统 RSS 格式"""
        traditional_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Traditional RSS Item</title>
                    <link>https://reddit.com/traditional</link>
                    <author>traditional_author</author>
                    <pubDate>Mon, 01 Jan 2023 12:00:00 GMT</pubDate>
                    <description>Traditional description</description>
                </item>
            </channel>
        </rss>'''
        
        posts = self.fetcher.parse_rss_content(traditional_xml, 'traditional', 5)
        
        # 验证解析结果
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['title'], 'Traditional RSS Item')
        self.assertEqual(posts[0]['link'], 'https://reddit.com/traditional')
        self.assertEqual(posts[0]['author'], 'traditional_author')

    def test_parse_rss_content_invalid_xml(self):
        """测试解析无效 XML"""
        invalid_xml = "Invalid XML content"
        posts = self.fetcher.parse_rss_content(invalid_xml, 'test', 5)
        
        # 验证结果
        self.assertEqual(len(posts), 0)

    def test_description_cleaning(self):
        """测试描述文本清理"""
        xml_with_html = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Post with HTML</title>
                <link href="https://reddit.com/test" />
                <content type="html">&lt;p&gt;This is a &lt;strong&gt;test&lt;/strong&gt; post with &lt;a href="http://example.com"&gt;links&lt;/a&gt; and very long description that should be truncated because it exceeds the maximum length allowed for description fields in our application which is set to 200 characters for performance reasons and to keep the content manageable for display purposes.&lt;/p&gt;</content>
            </entry>
        </feed>'''
        
        posts = self.fetcher.parse_rss_content(xml_with_html, 'test', 5)
        
        # 验证 HTML 标签被移除
        self.assertNotIn('<p>', posts[0]['description'])
        self.assertNotIn('<strong>', posts[0]['description'])
        self.assertIn('This is a test post', posts[0]['description'])
        
        # 验证长度限制
        self.assertLessEqual(len(posts[0]['description']), 203)  # 200 + "..."

    @patch.object(RedditFetcher, 'fetch_subreddit_rss')
    def test_fetch_multiple_subreddits(self, mock_fetch):
        """测试获取多个 subreddit"""
        # 模拟返回结果
        mock_fetch.side_effect = [
            [{'title': 'Post 1', 'subreddit': 'python'}],
            [{'title': 'Post 2', 'subreddit': 'programming'}],
            []  # 第三个 subreddit 返回空
        ]
        
        results = self.fetcher.fetch_multiple_subreddits(['python', 'programming', 'nonexistent'], 2)
        
        # 验证结果
        self.assertEqual(len(results), 2)  # 只有成功的 subreddit
        self.assertIn('python', results)
        self.assertIn('programming', results)
        self.assertNotIn('nonexistent', results)
        
        # 验证调用次数
        self.assertEqual(mock_fetch.call_count, 3)

    @patch.object(RedditFetcher, 'fetch_multiple_subreddits')
    def test_get_trending_posts(self, mock_fetch):
        """测试获取热门帖子"""
        # 模拟返回结果
        mock_fetch.return_value = {
            'python': [
                {'title': 'Python tutorial', 'subreddit': 'python', 'description': 'A great python tutorial'},
                {'title': 'Python news', 'subreddit': 'python', 'description': 'Latest python news'}
            ],
            'programming': [
                {'title': 'Programming guide', 'subreddit': 'programming', 'description': 'Short'}
            ]
        }
        
        trending = self.fetcher.get_trending_posts(['python', 'programming'], total_limit=5)
        
        # 验证结果
        self.assertEqual(len(trending), 3)
        
        # 验证分数计算和排序
        for post in trending:
            self.assertIn('score', post)
            self.assertGreater(post['score'], 0)
        
        # 验证按分数排序（第一个应该分数最高）
        self.assertGreaterEqual(trending[0]['score'], trending[1]['score'])
        self.assertGreaterEqual(trending[1]['score'], trending[2]['score'])

    def test_calculate_post_score(self):
        """测试帖子分数计算"""
        # 测试高分帖子（长度适中，包含关键词）
        high_score_post = {
            'title': 'Python tutorial guide - learn python programming',
            'description': 'This is a comprehensive tutorial about Python programming with detailed explanations and examples.'
        }
        score = self.fetcher._calculate_post_score(high_score_post)
        self.assertGreater(score, 20)  # 应该有较高分数
        
        # 测试低分帖子（标题太短）
        low_score_post = {
            'title': 'Short',
            'description': 'Short'
        }
        score = self.fetcher._calculate_post_score(low_score_post)
        self.assertLess(score, 10)  # 应该有较低分数


class TestFeishuNotifier(unittest.TestCase):
    """飞书通知器测试类"""

    def setUp(self):
        """测试前准备"""
        # 使用临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # 模拟环境变量
        with patch.dict(os.environ, {'FEISHU_WEBHOOK_URL': ''}):
            self.notifier = FeishuNotifier()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    def test_init_without_webhook(self):
        """测试未配置 webhook 时的初始化"""
        self.assertFalse(self.notifier.enabled)
        self.assertEqual(self.notifier.webhook_url, '')

    @patch.dict(os.environ, {'FEISHU_WEBHOOK_URL': 'https://test.webhook.com'})
    def test_init_with_webhook(self):
        """测试配置 webhook 时的初始化"""
        notifier = FeishuNotifier()
        self.assertTrue(notifier.enabled)
        self.assertEqual(notifier.webhook_url, 'https://test.webhook.com')

    def test_send_mock_message(self):
        """测试模拟发送消息"""
        test_posts = [
            {'title': 'Test Post 1', 'subreddit': 'test', 'link': 'https://reddit.com/test1'},
            {'title': 'Test Post 2', 'subreddit': 'python', 'link': 'https://reddit.com/test2'}
        ]
        
        result = self.notifier.send_message(
            title="Test Title",
            content="Test Content",
            posts=test_posts
        )
        
        self.assertTrue(result)

    @patch('reddit_daily_push.requests.post')
    @patch.dict(os.environ, {'FEISHU_WEBHOOK_URL': 'https://test.webhook.com'})
    def test_send_real_message_success(self, mock_post):
        """测试发送真实消息成功"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = FeishuNotifier()
        test_posts = [
            {'title': 'Test Post', 'subreddit': 'test', 'link': 'https://reddit.com/test'}
        ]
        
        result = notifier.send_message("Test Title", "Test Content", test_posts)
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # 验证请求参数
        call_args = mock_post.call_args
        self.assertEqual(call_args.kwargs['json']['msg_type'], 'interactive')
        self.assertIn('card', call_args.kwargs['json'])

    @patch('reddit_daily_push.requests.post')
    @patch.dict(os.environ, {'FEISHU_WEBHOOK_URL': 'https://test.webhook.com'})
    def test_send_real_message_failure(self, mock_post):
        """测试发送真实消息失败"""
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        notifier = FeishuNotifier()
        result = notifier.send_message("Test Title", "Test Content", [])
        
        self.assertFalse(result)

    @patch('reddit_daily_push.requests.post')
    @patch.dict(os.environ, {'FEISHU_WEBHOOK_URL': 'https://test.webhook.com'})
    def test_send_real_message_exception(self, mock_post):
        """测试发送真实消息异常"""
        # 模拟异常
        mock_post.side_effect = Exception("Network error")
        
        notifier = FeishuNotifier()
        result = notifier.send_message("Test Title", "Test Content", [])
        
        self.assertFalse(result)

    @patch('builtins.open', new_callable=mock_open)
    @patch('reddit_daily_push.Path.mkdir')
    def test_save_to_file(self, mock_mkdir, mock_file):
        """测试保存到文件"""
        test_posts = [
            {'title': 'Test Post', 'subreddit': 'test', 'link': 'https://reddit.com/test', 'description': 'Test description'}
        ]
        
        # 调用保存方法
        self.notifier._save_to_file("Test Title", "Test Content", test_posts)
        
        # 验证文件操作
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once()
        
        # 验证文件内容
        handle = mock_file()
        write_calls = handle.write.call_args_list
        written_content = ''.join(call.args[0] for call in write_calls)
        self.assertIn("Test Title", written_content)
        self.assertIn("Test Post", written_content)


class TestRedditDailyPusher(unittest.TestCase):
    """Reddit 每日推送器测试类"""

    def setUp(self):
        """测试前准备"""
        # 使用临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # 模拟项目根目录
        with patch('reddit_daily_push.project_root', self.project_root):
            self.pusher = RedditDailyPusher()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    @patch.object(RedditFetcher, 'get_trending_posts')
    @patch.object(FeishuNotifier, 'send_message')
    def test_fetch_and_push_success(self, mock_send, mock_get_posts):
        """测试成功获取并推送"""
        # 模拟返回结果
        mock_posts = [
            {'title': 'Test Post 1', 'subreddit': 'python', 'link': 'https://reddit.com/test1'},
            {'title': 'Test Post 2', 'subreddit': 'programming', 'link': 'https://reddit.com/test2'}
        ]
        mock_get_posts.return_value = mock_posts
        mock_send.return_value = True
        
        result = self.pusher.fetch_and_push()
        
        self.assertTrue(result)
        mock_get_posts.assert_called_once()
        mock_send.assert_called_once()
        
        # 验证发送的消息内容
        send_args = mock_send.call_args
        self.assertIn("Reddit 技术资讯日报", send_args[0][0])
        self.assertIn("热门技术内容", send_args[0][1])

    @patch.object(RedditFetcher, 'get_trending_posts')
    def test_fetch_and_push_no_posts(self, mock_get_posts):
        """测试没有获取到帖子时"""
        mock_get_posts.return_value = []
        
        result = self.pusher.fetch_and_push()
        
        self.assertFalse(result)

    @patch.object(RedditFetcher, 'get_trending_posts')
    @patch.object(FeishuNotifier, 'send_message')
    def test_fetch_and_push_send_failure(self, mock_send, mock_get_posts):
        """测试发送消息失败"""
        mock_posts = [{'title': 'Test Post', 'subreddit': 'test', 'link': 'https://reddit.com/test'}]
        mock_get_posts.return_value = mock_posts
        mock_send.return_value = False
        
        result = self.pusher.fetch_and_push()
        
        self.assertFalse(result)

    @patch.object(RedditFetcher, 'get_trending_posts')
    def test_fetch_and_push_exception(self, mock_get_posts):
        """测试获取和推送过程中出现异常"""
        mock_get_posts.side_effect = Exception("Test error")
        
        result = self.pusher.fetch_and_push()
        
        self.assertFalse(result)

    @patch('reddit_daily_push.json.dump')
    @patch('reddit_daily_push.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_push_record(self, mock_file, mock_mkdir, mock_json_dump):
        """测试保存推送记录"""
        test_posts = [
            {'title': 'Test Post', 'subreddit': 'test', 'link': 'https://reddit.com/test'}
        ]
        
        self.pusher._save_push_record(test_posts)
        
        # 验证目录创建
        mock_mkdir.assert_called_once()
        
        # 验证文件操作
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
        
        # 验证 JSON 数据结构
        json_args = mock_json_dump.call_args
        record_data = json_args[0][0]
        self.assertIn('push_time', record_data)
        self.assertIn('post_count', record_data)
        self.assertIn('subreddits', record_data)
        self.assertIn('posts', record_data)
        self.assertEqual(record_data['post_count'], 1)
        self.assertIn('test', record_data['subreddits'])

    def test_run_once(self):
        """测试运行一次"""
        with patch.object(self.pusher, 'fetch_and_push', return_value=True) as mock_fetch:
            result = self.pusher.run_once()
            
            self.assertTrue(result)
            mock_fetch.assert_called_once()

    def test_run_once_failure(self):
        """测试运行一次失败"""
        with patch.object(self.pusher, 'fetch_and_push', return_value=False) as mock_fetch:
            result = self.pusher.run_once()
            
            self.assertFalse(result)
            mock_fetch.assert_called_once()


if __name__ == '__main__':
    unittest.main()