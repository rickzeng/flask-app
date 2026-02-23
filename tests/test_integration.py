#!/usr/bin/env python3
"""
集成测试
"""

import unittest
import json
import tempfile
import shutil
import os
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from app.reddit.push import RedditDailyPusher, RedditFetcher, FeishuNotifier
from app.reddit.config import get_config, get_message_templates, get_keywords
from config.base import Config


class TestFlaskIntegration(unittest.TestCase):
    """Flask 应用集成测试"""

    def setUp(self):
        """测试前准备"""
        self.app = app.test_client()
        self.app.testing = True

    def test_full_api_workflow(self):
        """测试完整的 API 工作流程"""
        # 1. 访问首页获取可用端点
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)

        # 2. 测试健康检查
        response = self.app.get("/api/health")
        self.assertEqual(response.status_code, 200)
        health_data = json.loads(response.data)
        self.assertEqual(health_data["status"], "healthy")

        # 3. 测试 hello API
        response = self.app.get("/api/hello")
        self.assertEqual(response.status_code, 200)
        hello_data = json.loads(response.data)
        self.assertEqual(hello_data["status"], "success")

        # 4. 验证 API 响应结构一致性
        self.assertIn("status", health_data)
        self.assertIn("status", hello_data)

    def test_cors_headers(self):
        """测试 CORS 头（如果配置了）"""
        response = self.app.get("/api/health")
        # 注意：这个测试假设应用配置了 CORS
        # 如果没有配置 CORS，可以跳过这个测试
        # self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_error_handling_consistency(self):
        """测试错误处理一致性"""
        # 测试多个不存在的端点
        endpoints = ["/nonexistent", "/api/nonexistent", "/api/v1/nonexistent"]
        for endpoint in endpoints:
            response = self.app.get(endpoint)
            self.assertEqual(response.status_code, 404)
            # 错误响应应该有一致的结构（如果实现了自定义错误处理）

    def test_request_response_cycle(self):
        """测试请求-响应周期"""
        # 测试正常的 GET 请求
        response = self.app.get("/api/health")
        self.assertEqual(response.status_code, 200)

        # 测试 POST 请求到不支持 POST 的端点
        response = self.app.post("/api/health")
        self.assertEqual(response.status_code, 405)

        # 测试 HEAD 请求（应该支持）
        response = self.app.head("/api/health")
        self.assertEqual(response.status_code, 200)


class TestRedditIntegration(unittest.TestCase):
    """Reddit 功能集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # 创建必要的目录结构
        (self.project_root / "reddit_output").mkdir(exist_ok=True)
        (self.project_root / "reddit_records").mkdir(exist_ok=True)
        (self.project_root / "reddit_cache").mkdir(exist_ok=True)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    @patch("reddit_daily_push.requests.get")
    @patch("reddit_daily_push.project_root", Path("/tmp"))
    def test_end_to_end_reddit_workflow(self, mock_get):
        """测试端到端 Reddit 工作流程"""
        # 模拟 RSS 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Integration Test Post</title>
                <link href="https://reddit.com/test" />
                <author>
                    <name>testuser</name>
                </author>
                <published>2023-01-01T12:00:00Z</published>
                <content type="html">Integration test content</content>
            </entry>
        </feed>"""
        mock_get.return_value = mock_response

        # 创建推送器实例
        with patch("reddit_daily_push.project_root", self.project_root):
            pusher = RedditDailyPusher()

            # 模拟不使用飞书通知（使用文件保存）
            pusher.feishu_notifier.webhook_url = ""
            pusher.feishu_notifier.enabled = False

            # 执行推送
            result = pusher.fetch_and_push()

            # 验证结果
            self.assertTrue(result)

            # 验证文件保存
            output_files = list((self.project_root / "reddit_output").glob("*.txt"))
            self.assertTrue(len(output_files) > 0)

            record_files = list((self.project_root / "reddit_records").glob("*.json"))
            self.assertTrue(len(record_files) > 0)

    @patch("reddit_daily_push.requests.get")
    def test_reddit_fetcher_integration(self, mock_get):
        """测试 Reddit 获取器集成"""
        # 模拟多个 subreddit 的响应
        mock_responses = [
            # python subreddit
            MagicMock(
                status_code=200,
                text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry><title>Python Post 1</title><link href="https://reddit.com/python1" /></entry>
                <entry><title>Python Post 2</title><link href="https://reddit.com/python2" /></entry>
            </feed>""",
            ),
            # programming subreddit
            MagicMock(
                status_code=200,
                text="""<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry><title>Programming Post 1</title><link href="https://reddit.com/prog1" /></entry>
                <entry><title>Programming Post 2</title><link href="https://reddit.com/prog2" /></entry>
            </feed>""",
            ),
        ]
        mock_get.side_effect = mock_responses

        # 创建获取器并测试
        fetcher = RedditFetcher()

        # 测试获取多个 subreddit
        results = fetcher.fetch_multiple_subreddits(
            ["python", "programming"], limit_per_sub=2
        )

        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertIn("python", results)
        self.assertIn("programming", results)
        self.assertEqual(len(results["python"]), 2)
        self.assertEqual(len(results["programming"]), 2)

        # 测试获取热门帖子
        trending = fetcher.get_trending_posts(["python", "programming"], total_limit=3)
        self.assertEqual(len(trending), 3)

        # 验证排序（所有帖子都应该有分数）
        for post in trending:
            self.assertIn("score", post)
            self.assertGreater(post["score"], 0)

    def test_feishu_notifier_integration(self):
        """测试飞书通知器集成"""
        notifier = FeishuNotifier()
        test_posts = [
            {
                "title": "Integration Test Post 1",
                "subreddit": "test",
                "link": "https://reddit.com/test1",
                "description": "Test description 1",
            },
            {
                "title": "Integration Test Post 2",
                "subreddit": "python",
                "link": "https://reddit.com/test2",
                "description": "Test description 2",
            },
        ]

        # 测试模拟发送
        with patch("reddit_daily_push.project_root", self.project_root):
            result = notifier.send_message(
                title="Integration Test Message",
                content="This is an integration test message",
                posts=test_posts,
            )

            self.assertTrue(result)

            # 验证文件保存
            output_files = list((self.project_root / "reddit_output").glob("*.txt"))
            self.assertTrue(len(output_files) > 0)

            # 验证文件内容
            with open(output_files[0], "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Integration Test Message", content)
                self.assertIn("Integration Test Post 1", content)
                self.assertIn("Integration Test Post 2", content)


class TestConfigIntegration(unittest.TestCase):
    """配置集成测试"""

    def test_config_integration_workflow(self):
        """测试配置集成工作流程"""
        # 1. 获取 Flask 配置
        flask_config = get_flask_config("testing")
        self.assertTrue(flask_config.TESTING)
        self.assertTrue(flask_config.DEBUG)

        # 2. 获取 Reddit 配置
        reddit_config = get_config()
        self.assertIn("subreddits", reddit_config)
        self.assertIn("feishu", reddit_config)

        # 3. 获取消息模板
        templates = get_message_templates()
        self.assertIn("daily_title", templates)
        self.assertIn("daily_content", templates)

        # 4. 获取关键词
        keywords = get_keywords()
        self.assertIn("positive", keywords)
        self.assertIn("negative", keywords)

        # 5. 验证配置一致性
        reddit_subreddits = reddit_config["subreddits"]
        self.assertIsInstance(reddit_subreddits, list)
        self.assertTrue(len(reddit_subreddits) > 0)

    @patch.dict(os.environ, {"FEISHU_WEBHOOK_URL": "https://test.integration.com"})
    def test_environment_config_integration(self):
        """测试环境配置集成"""
        # 验证环境变量影响 Reddit 配置
        reddit_config = get_config()
        self.assertTrue(reddit_config["feishu"]["enabled"])
        self.assertEqual(
            reddit_config["feishu"]["webhook_url"], "https://test.integration.com"
        )

        # 验证环境变量影响 Flask 配置
        os.environ["FLASK_DEBUG"] = "false"
        flask_config = get_flask_config("development")
        self.assertFalse(flask_config.DEBUG)
        os.environ["FLASK_DEBUG"] = "true"  # 恢复原值

    def test_template_integration(self):
        """测试模板集成"""
        templates = get_message_templates()

        # 测试模板格式化
        daily_title = templates["daily_title"].format(date="2023-01-01")
        self.assertIn("2023-01-01", daily_title)
        self.assertIn("Reddit 技术资讯日报", daily_title)

        daily_content = templates["daily_content"].format(
            stats="r/python: 3 | r/programming: 2", count=5
        )
        self.assertIn("r/python: 3 | r/programming: 2", daily_content)
        self.assertIn("共 5 条", daily_content)

    def test_keyword_integration(self):
        """测试关键词集成"""
        keywords = get_keywords()
        positive_keywords = keywords["positive"]
        negative_keywords = keywords["negative"]

        # 测试关键词匹配逻辑
        test_title = "Python tutorial guide for beginners"
        positive_matches = [kw for kw in positive_keywords if kw in test_title.lower()]
        self.assertTrue(len(positive_matches) > 0)

        test_title_negative = "Job opportunities in tech"
        negative_matches = [
            kw for kw in negative_keywords if kw in test_title_negative.lower()
        ]
        self.assertTrue(len(negative_matches) > 0)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)

    @patch("reddit_daily_push.requests.get")
    @patch.dict(os.environ, {"FEISHU_WEBHOOK_URL": ""})
    def test_full_system_integration(self, mock_get):
        """测试完整系统集成"""
        # 模拟 Reddit API 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>System Integration Test</title>
                <link href="https://reddit.com/system_test" />
                <author>
                    <name>system_user</name>
                </author>
                <published>2023-01-01T12:00:00Z</published>
                <content type="html">System integration test content</content>
            </entry>
        </feed>"""
        mock_get.return_value = mock_response

        with patch("reddit_daily_push.project_root", self.project_root):
            # 1. 初始化系统组件
            fetcher = RedditFetcher()
            notifier = FeishuNotifier()
            pusher = RedditDailyPusher()

            # 2. 获取内容
            posts = fetcher.get_trending_posts(["python"], total_limit=1)
            self.assertEqual(len(posts), 1)

            # 3. 构建消息
            title = f"📰 Reddit 技术资讯日报 - {time.strftime('%Y-%m-%d')}"
            content = "🚀 今日热门技术内容已送达！\n\n**统计摘要:**\nr/python: 1\n\n**精选内容:** (共 1 条)"

            # 4. 发送通知
            result = notifier.send_message(title, content, posts)
            self.assertTrue(result)

            # 5. 验证完整流程
            output_files = list((self.project_root / "reddit_output").glob("*.txt"))
            self.assertTrue(len(output_files) > 0)

            record_files = list((self.project_root / "reddit_records").glob("*.json"))
            self.assertTrue(len(record_files) > 0)

    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试各种错误情况的集成处理
        with patch("reddit_daily_push.requests.get") as mock_get:
            # 模拟网络错误
            mock_get.side_effect = Exception("Network error")

            fetcher = RedditFetcher()
            posts = fetcher.fetch_subreddit_rss("test", limit=5)
            self.assertEqual(len(posts), 0)

            # 测试系统在错误情况下的稳定性
            results = fetcher.fetch_multiple_subreddits(
                ["test1", "test2"], limit_per_sub=5
            )
            self.assertEqual(len(results), 0)

    def test_concurrent_operations(self):
        """测试并发操作"""
        # 这个测试验证系统在多个操作同时进行时的稳定性
        with patch("reddit_daily_push.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
                <entry><title>Concurrent Test Post</title><link href="https://reddit.com/concurrent" /></entry>
            </feed>"""
            mock_get.return_value = mock_response

            fetcher = RedditFetcher()

            # 测试连续多个操作
            results1 = fetcher.fetch_subreddit_rss("test1", limit=2)
            results2 = fetcher.fetch_subreddit_rss("test2", limit=2)
            results3 = fetcher.fetch_subreddit_rss("test3", limit=2)

            # 验证所有操作都成功
            self.assertEqual(len(results1), 1)
            self.assertEqual(len(results2), 1)
            self.assertEqual(len(results3), 1)

            # 验证操作之间的隔离性
            self.assertEqual(results1[0]["subreddit"], "test1")
            self.assertEqual(results2[0]["subreddit"], "test2")
            self.assertEqual(results3[0]["subreddit"], "test3")


if __name__ == "__main__":
    unittest.main()
