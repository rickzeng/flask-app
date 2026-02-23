#!/bin/bash
# 安装 Reddit 每日推送的 cron 任务

echo "📅 安装 Reddit 每日推送 cron 任务"
echo "======================================"

# 项目目录
PROJECT_DIR="/home/ubuntu/flask-app"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"
MAIN_SCRIPT="$PROJECT_DIR/app/reddit/main.py"
LOG_FILE="$PROJECT_DIR/reddit_cron.log"

# 创建 cron 任务内容
CRON_CONTENT="# Reddit 每日推送任务
# 每天中午12点运行
0 12 * * * cd $PROJECT_DIR && $VENV_PYTHON $MAIN_SCRIPT --once >> $LOG_FILE 2>&1

# 测试任务（每30分钟运行一次，用于调试）
# */30 * * * * cd $PROJECT_DIR && $VENV_PYTHON $MAIN_SCRIPT --once >> $PROJECT_DIR/reddit_test.log 2>&1
"

echo "Cron 任务配置:"
echo "--------------"
echo "$CRON_CONTENT"
echo "--------------"

# 保存到文件
echo "$CRON_CONTENT" > "$PROJECT_DIR/reddit_cron_job.txt"

echo ""
echo "📝 安装说明:"
echo "1. 编辑当前用户的 crontab:"
echo "   crontab -e"
echo ""
echo "2. 添加以下行:"
echo "   0 12 * * * cd $PROJECT_DIR && $VENV_PYTHON $MAIN_SCRIPT --once >> $LOG_FILE 2>&1"
echo ""
echo "3. 保存并退出编辑器"
echo ""
echo "4. 验证安装:"
echo "   crontab -l"
echo ""
echo "5. 测试任务 (可选):"
echo "   cd $PROJECT_DIR && $VENV_PYTHON $MAIN_SCRIPT --once"
echo ""
echo "📋 文件位置:"
echo "   项目目录: $PROJECT_DIR"
echo "   Python: $VENV_PYTHON"
echo "   主脚本: $MAIN_SCRIPT"
echo "   日志文件: $LOG_FILE"
echo "   Cron 配置: $PROJECT_DIR/reddit_cron_job.txt"
echo ""
echo "✅ 安装说明已保存到: $PROJECT_DIR/reddit_cron_job.txt"

# 可选：自动安装（需要确认）
read -p "是否自动安装到 crontab？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 备份现有 crontab
    crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || true
    
    # 添加新任务
    (crontab -l 2>/dev/null; echo "# Reddit 每日推送任务"; echo "0 12 * * * cd $PROJECT_DIR && $VENV_PYTHON $MAIN_SCRIPT --once >> $LOG_FILE 2>&1") | crontab -
    
    echo "✅ Cron 任务已安装"
    echo "当前 crontab:"
    crontab -l
else
    echo "⚠️  请手动安装 cron 任务"
fi