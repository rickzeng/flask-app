#!/usr/bin/env python3
"""
Reddit 推送功能测试
"""

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.reddit.push import RedditFetcher, FeishuNotifier
from app.reddit.config import REDDIT_CONFIG


class TestRedditFetcher(unittest.TestCase):
    """Reddit 内容获取器测试"""

    def setUp(self):
        """测试前准备"""
        self.fetcher = RedditFetcher(proxy_url="http://127.0.0.1:7890")

    @patch("reddit_daily_push.requests.get")
    def test_fetch_subreddit_success(self, mock_get):
        """测试成功获取 subreddit 内容"""
        # 模拟成功的 RSS 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = """
        <rss>
            <channel>
                <item>
                    <title>Test Post 1</title>
                    <link>https://reddit.com/r/test/comments/1</link>
                    <description>Test description 1</description>
                </item>
                <item>
                    <title>Test Post 2</title>
                    <link>https://reddit.com/r/test/comments/2</link>
                    <description>Test description 2</description>
                </item>
            </channel>
        </rss>
        """
        mock_get.return_value = mock_response

        content = self.fetcher.fetch_subreddit("test", limit=2)

        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]["title"], "Test Post 1")
        self.assertEqual(content[0]["link"], "https://reddit.com/r/test/comments/1")
        self.assertEqual(content[1]["title"], "Test Post 2")

    @patch("reddit_daily_push.requests.get")
    def test_fetch_subreddit_failure(self, mock_get):
        """测试获取 subreddit 失败"""
        # 模拟失败的响应
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        content = self.fetcher.fetch_subreddit("test")

        self.assertEqual(len(content), 0)

    @patch("reddit_daily_push.requests.get")
    def test_fetch_subreddit_timeout(self, mock_get):
        """测试获取 subreddit 超时"""
        mock_get.side_effect = TimeoutError("Request timeout")

        content = self.fetcher.fetch_subreddit("test")

        self.assertEqual(len(content), 0)

    def test_parse_rss_content(self):
        """测试解析 RSS 内容"""
        rss_content = """
        <rss>
            <channel>
                <item>
                    <title>Test Post</title>
                    <link>https://reddit.com/r/test/comments/1</link>
                    <description>Test &lt;b&gt;description&lt;/b&gt; with &amp; entities</description>
                </item>
            </channel>
        </rss>
        """

        content = self.fetcher.parse_rss_content(rss_content, "test", 1)

        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["title"], "Test Post")
        self.assertEqual(content[0]["link"], "https://reddit.com/r/test/comments/1")
        self.assertEqual(content[0]["description"], "Test description with & entities")
        self.assertEqual(content[0]["source"], "test")

    def test_clean_html(self):
        """测试清理 HTML"""
        html_content = "Test &lt;b&gt;bold&lt;/b&gt; and &amp; entities"
        cleaned = self.fetcher.clean_html(html_content)

        self.assertEqual(cleaned, "Test bold and & entities")

    def test_filter_content_keywords(self):
        """测试关键词过滤"""
        content = [
            {"title": "Python tutorial for beginners", "score": 100},
            {"title": "Java vs Python comparison", "score": 80},
            {"title": "Random post about cats", "score": 50},
        ]

        filtered = self.fetcher.filter_content_by_keywords(
            content, ["python", "tutorial"]
        )

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["title"], "Python tutorial for beginners")
        self.assertEqual(filtered[1]["title"], "Java vs Python comparison")

    def test_sort_content_by_score(self):
        """测试按分数排序"""
        content = [
            {"title": "Post 1", "score": 50},
            {"title": "Post 2", "score": 100},
            {"title": "Post 3", "score": 75},
        ]

        sorted_content = self.fetcher.sort_content_by_score(content)

        self.assertEqual(sorted_content[0]["title"], "Post 2")
        self.assertEqual(sorted_content[0]["score"], 100)
        self.assertEqual(sorted_content[1]["title"], "Post 3")
        self.assertEqual(sorted_content[2]["title"], "Post 1")


class TestFeishuNotifier(unittest.TestCase):
    """Reddit 内容通知器测试"""

    def setUp(self):
        """测试前准备"""
        self.notifier = FeishuNotifier()

    def test_format_message(self):
        """测试消息格式化"""
        content = [
            {
                "title": "Test Post 1",
                "link": "https://reddit.com/r/test/comments/1",
                "source": "test",
                "description": "Test description 1",
            },
            {
                "title": "Test Post 2",
                "link": "https://reddit.com/r/test/comments/2",
                "source": "test",
                "description": "Test description 2",
            },
        ]

        message = self.notifier.format_message(content)

        self.assertIn("Test Post 1", message)
        self.assertIn("https://reddit.com/r/test/comments/1", message)
        self.assertIn("来源: test", message)
        self.assertIn("Test Post 2", message)

    def test_format_message_empty(self):
        """测试空内容消息格式化"""
        message = self.notifier.format_message([])

        self.assertIn("今日无新内容", message)

    @patch("reddit_daily_push.requests.post")
    def test_send_to_feishu_success(self, mock_post):
        """测试成功发送到飞书"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"StatusCode": 0, "StatusMessage": "success"}
        mock_post.return_value = mock_response

        message = "Test message"
        result = self.notifier.send_to_feishu(message, "test_webhook")

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("reddit_daily_push.requests.post")
    def test_send_to_feishu_failure(self, mock_post):
        """测试发送到飞书失败"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        message = "Test message"
        result = self.notifier.send_to_feishu(message, "test_webhook")

        self.assertFalse(result)

    @patch("reddit_daily_push.requests.post")
    def test_send_to_feishu_timeout(self, mock_post):
        """测试发送到飞书超时"""
        mock_post.side_effect = TimeoutError("Request timeout")

        message = "Test message"
        result = self.notifier.send_to_feishu(message, "test_webhook")

        self.assertFalse(result)

    def test_save_to_file(self):
        """测试保存到文件"""
        message = "Test message content"

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs") as mock_makedirs:
                result = self.notifier.save_to_file(message, "/tmp/test_output.txt")

                self.assertTrue(result)
                mock_makedirs.assert_called_once_with("/tmp", exist_ok=True)
                mock_file.assert_called_once_with(
                    "/tmp/test_output.txt", "w", encoding="utf-8"
                )

                # 检查写入的内容
                handle = mock_file()
                handle.write.assert_called_once_with(message)


class TestRedditConfig(unittest.TestCase):
    """Reddit 配置测试"""

    def test_config_structure(self):
        """测试配置结构"""
        self.assertIsInstance(REDDIT_CONFIG, dict)
        self.assertIn("subreddits", REDDIT_CONFIG)
        self.assertIn("keywords", REDDIT_CONFIG)
        self.assertIn("max_posts_per_subreddit", REDDIT_CONFIG)
        self.assertIn("feishu_webhook_url", REDDIT_CONFIG)

    def test_subreddits_list(self):
        """测试 subreddits 列表"""
        subreddits = REDDIT_CONFIG["subreddits"]
        self.assertIsInstance(subreddits, list)
        self.assertGreater(len(subreddits), 0)

        # 检查是否包含预期的 subreddits
        expected_subreddits = ["programming", "technology", "python"]
        for subreddit in expected_subreddits:
            self.assertIn(subreddit, subreddits)

    def test_keywords_list(self):
        """测试关键词列表"""
        keywords = REDDIT_CONFIG["keywords"]
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)

        # 检查是否包含预期的关键词
        expected_keywords = ["python", "flask", "docker", "linux"]
        for keyword in expected_keywords:
            self.assertIn(keyword, keywords)


if __name__ == "__main__":
    unittest.main()
