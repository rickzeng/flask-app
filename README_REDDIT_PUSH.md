# Reddit 每日推送系统

## 📋 项目概述

这是一个自动化的 Reddit 内容获取和推送系统，每天中午12点获取指定的技术类 subreddit 内容，并通过飞书推送给用户。

## 🎯 功能特性

- ✅ **定时获取**: 每天中午12点自动获取 Reddit 内容
- ✅ **多 subreddit 支持**: 同时监控多个技术社区
- ✅ **智能筛选**: 根据关键词和热度筛选内容
- ✅ **飞书推送**: 通过飞书 webhook 发送精美消息卡片
- ✅ **本地存储**: 所有获取的内容本地保存，便于查阅
- ✅ **灵活配置**: 可自定义关注的 subreddit、推送时间等

## 🏗️ 系统架构

```
用户 ← 飞书消息 ← 推送系统 ← Reddit RSS
                    ↑
                配置管理 + 日志记录
```

## 📁 文件结构

```
flask-app/
├── reddit_daily_push.py      # 主逻辑脚本
├── reddit_push_main.py       # 入口脚本
├── reddit_config.py          # 配置文件
├── reddit_config.py          # 配置模块
├── setup_reddit_push.sh      # 安装脚本
├── README_REDDIT_PUSH.md     # 本文档
├── reddit_output/            # 推送输出目录
├── reddit_records/           # 推送记录目录
└── reddit_cache/             # 缓存目录
```

## 🚀 快速开始

### 1. 安装依赖
```bash
# 进入项目目录
cd /home/ubuntu/flask-app

# 运行安装脚本
chmod +x setup_reddit_push.sh
./setup_reddit_push.sh
```

### 2. 配置飞书 webhook (可选)
```bash
# 设置环境变量
export FEISHU_WEBHOOK_URL="你的飞书webhook地址"

# 或编辑 .env.reddit 文件
nano .env.reddit
```

### 3. 测试运行
```bash
# 测试 Reddit 访问
python3 reddit_push_main.py --test

# 立即运行一次推送
python3 reddit_push_main.py --once
```

### 4. 设置定时任务
```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天中午12点运行）
0 12 * * * cd /home/ubuntu/flask-app && python3 reddit_push_main.py --once >> reddit_cron.log 2>&1
```

## ⚙️ 配置说明

### 主要配置项

#### 1. 关注的 subreddit
编辑 `reddit_config.py` 中的 `REDDIT_CONFIG['subreddits']`:
```python
'subreddits': [
    'programming',      # 编程
    'technology',       # 技术
    'python',           # Python
    'webdev',           # 网页开发
    'linux',            # Linux
    'opensource',       # 开源
    # 添加更多...
],
```

#### 2. 推送时间
编辑 `reddit_config.py` 中的 `REDDIT_CONFIG['push_time']`:
```python
'push_time': '12:00',  # 每天中午12点
```

#### 3. 代理设置
编辑 `.env.reddit` 文件:
```bash
REDDIT_PROXY_URL=http://127.0.0.1:7890  # Clash 代理地址
```

#### 4. 飞书配置
设置环境变量或编辑 `.env.reddit`:
```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx
```

## 📊 推送内容示例

### 飞书消息卡片
```
📰 Reddit 技术资讯日报 - 2026-02-17

🚀 今日热门技术内容已送达！

统计摘要:
r/programming: 3 | r/technology: 2 | r/python: 3 | r/webdev: 2

精选内容: (共 10 条)

1. Python 3.13 新特性预览
   来源: r/python
   链接: https://reddit.com/...

2. 2026年 Web 开发趋势预测
   来源: r/webdev
   链接: https://reddit.com/...

3. Linux 内核 6.12 发布
   来源: r/linux
   链接: https://reddit.com/...
```

### 本地输出文件
每次推送都会在 `reddit_output/` 目录生成文本文件，包含完整内容。

## 🔧 高级功能

### 1. 守护进程模式
```bash
# 启动守护进程（适合长期运行）
python3 reddit_push_main.py --daemon
```

### 2. Systemd 服务
```bash
# 安装为系统服务
sudo cp reddit-push.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start reddit-push
sudo systemctl enable reddit-push

# 查看服务状态
sudo systemctl status reddit-push
```

### 3. 自定义消息模板
编辑 `reddit_config.py` 中的 `MESSAGE_TEMPLATES`:
```python
MESSAGE_TEMPLATES = {
    'daily_title': "📰 Reddit 技术资讯日报 - {date}",
    'daily_content': """🚀 今日热门技术内容已送达！
    
**统计摘要:**
{stats}
    
**精选内容:** (共 {count} 条)
""",
}
```

### 4. 关键词过滤
编辑 `reddit_config.py` 中的 `KEYWORDS`:
```python
KEYWORDS = {
    'positive': [  # 优先显示
        'tutorial', 'guide', 'how to', 'learn',
        'news', 'update', 'release',
    ],
    'negative': [  # 过滤掉
        'job', 'hire', 'career', 'salary',
        'political', 'controversial',
    ]
}
```

## 🐛 故障排除

### 常见问题

#### 1. Reddit 访问失败
```bash
# 检查代理
curl -x http://127.0.0.1:7890 https://www.reddit.com/r/python/.rss

# 检查网络
ping 8.8.8.8
```

#### 2. 飞书推送失败
```bash
# 检查 webhook 配置
echo $FEISHU_WEBHOOK_URL

# 测试 webhook
curl -X POST -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"test"}}' \
  $FEISHU_WEBHOOK_URL
```

#### 3. 定时任务不执行
```bash
# 检查 crontab
crontab -l

# 查看 cron 日志
grep CRON /var/log/syslog

# 手动测试
python3 reddit_push_main.py --once
```

#### 4. 内存/CPU 使用过高
```bash
# 查看进程
ps aux | grep reddit_push

# 调整获取数量
# 编辑 reddit_config.py，减少 max_posts_per_sub 和 total_posts_limit
```

### 日志查看
```bash
# 查看推送日志
tail -f reddit_push.log

# 查看 cron 执行日志
tail -f reddit_cron.log

# 查看错误日志
grep ERROR reddit_push.log
```

## 📈 监控和维护

### 1. 监控推送状态
```bash
# 查看最近推送
ls -la reddit_output/

# 查看推送统计
find reddit_records/ -name "*.json" | wc -l
```

### 2. 清理旧文件
```bash
# 清理30天前的输出文件
find reddit_output/ -type f -mtime +30 -delete

# 清理旧记录
find reddit_records/ -type f -mtime +90 -delete
```

### 3. 备份配置
```bash
# 备份配置文件
tar czf reddit_config_backup_$(date +%Y%m%d).tar.gz \
  reddit_config.py .env.reddit reddit_cron_setup.txt
```

## 🔄 更新和扩展

### 1. 添加新的 subreddit
1. 编辑 `reddit_config.py`
2. 添加 subreddit 名称到列表
3. 重启服务或等待下次推送

### 2. 修改推送频率
```bash
# 修改 crontab
# 每小时推送: 0 * * * *
# 每6小时推送: 0 */6 * * *
# 工作日推送: 0 12 * * 1-5
```

### 3. 集成到 Flask 应用
```python
# 在 app.py 中添加 API 端点
@app.route('/api/reddit/push', methods=['POST'])
def reddit_push():
    from reddit_daily_push import RedditDailyPusher
    pusher = RedditDailyPusher()
    success = pusher.run_once()
    return jsonify({'success': success})
```

## 📞 支持

### 问题反馈
1. 查看日志文件: `reddit_push.log`
2. 检查配置文件: `reddit_config.py`
3. 测试网络连接

### 获取帮助
- 查看本文档
- 检查错误日志
- 测试各个组件

## 📄 许可证

本项目基于 MIT 许可证开源。

## 🙏 致谢

- Reddit 提供丰富的技术社区内容
- 飞书提供消息推送接口
- OpenClaw 项目提供基础设施支持

---
**最后更新**: 2026-02-17  
**版本**: 1.0.0  
**维护者**: OpenClaw 助手