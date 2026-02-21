#!/bin/bash
# Reddit 每日推送安装脚本

set -e

echo "🔧 安装 Reddit 每日推送系统"
echo "=============================="

# 检查 Python 环境
echo "1. 检查 Python 环境..."
python3 --version
pip3 --version

# 安装依赖
echo -e "\n2. 安装 Python 依赖..."
pip3 install requests schedule

# 创建必要的目录
echo -e "\n3. 创建目录结构..."
mkdir -p reddit_output reddit_records reddit_cache

# 设置文件权限
echo -e "\n4. 设置文件权限..."
chmod +x reddit_daily_push.py reddit_push_main.py

# 测试 Reddit 访问
echo -e "\n5. 测试 Reddit 访问..."
python3 -c "
import requests
try:
    response = requests.get(
        'https://www.reddit.com/r/python/.rss',
        proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'},
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    if response.status_code == 200:
        print('✅ Reddit 访问测试成功')
    else:
        print('❌ Reddit 访问测试失败:', response.status_code)
except Exception as e:
    print('❌ Reddit 访问测试异常:', e)
"

# 配置飞书 webhook（可选）
echo -e "\n6. 配置飞书 webhook (可选)..."
if [ -z "$FEISHU_WEBHOOK_URL" ]; then
    echo "   未设置 FEISHU_WEBHOOK_URL 环境变量"
    echo "   将使用模拟发送模式"
    echo "   要启用真实推送，请设置:"
    echo "   export FEISHU_WEBHOOK_URL='你的飞书webhook地址'"
else
    echo "   已检测到飞书 webhook 配置"
fi

# 创建环境变量文件
echo -e "\n7. 创建环境配置..."
cat > .env.reddit << EOF
# Reddit 推送配置
FEISHU_WEBHOOK_URL=${FEISHU_WEBHOOK_URL:-}
REDDIT_PROXY_URL=http://127.0.0.1:7890
PUSH_TIME=12:00
EOF

echo "   环境配置已保存到 .env.reddit"

# 测试脚本运行
echo -e "\n8. 测试脚本运行..."
python3 reddit_push_main.py --test

# 设置 cron 任务
echo -e "\n9. 设置 cron 定时任务..."
cat > reddit_cron_setup.txt << EOF
# Reddit 每日推送 cron 配置
# 每天中午12点运行
0 12 * * * cd $(pwd) && python3 reddit_push_main.py --once >> reddit_cron.log 2>&1

# 添加到 crontab 的命令:
# crontab -e
# 然后添加以上行
EOF

echo "   Cron 配置已保存到 reddit_cron_setup.txt"

# 创建 systemd 服务文件（可选）
echo -e "\n10. 创建 systemd 服务文件 (可选)..."
cat > reddit-push.service << EOF
[Unit]
Description=Reddit Daily Push Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env.reddit
ExecStart=/usr/bin/python3 $(pwd)/reddit_push_main.py --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "   Systemd 服务文件已创建: reddit-push.service"
echo "   安装命令: sudo cp reddit-push.service /etc/systemd/system/"
echo "   启动命令: sudo systemctl start reddit-push"
echo "   启用自启: sudo systemctl enable reddit-push"

# 使用说明
echo -e "\n📋 安装完成！使用说明:"
echo "=============================="
echo "立即测试推送: python3 reddit_push_main.py --once"
echo "启动守护进程: python3 reddit_push_main.py --daemon"
echo "查看日志: tail -f reddit_push.log"
echo "查看输出: ls reddit_output/"
echo ""
echo "📅 定时任务设置:"
echo "1. 编辑 crontab: crontab -e"
echo "2. 添加行: 0 12 * * * cd $(pwd) && python3 reddit_push_main.py --once >> reddit_cron.log 2>&1"
echo ""
echo "🛠️ 自定义配置:"
echo "编辑 reddit_config.py 修改关注的 subreddit"
echo "编辑 .env.reddit 修改推送时间和代理设置"

echo -e "\n🎉 安装完成！"