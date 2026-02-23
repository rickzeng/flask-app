#!/usr/bin/env python3
"""
Flask 应用程序启动脚本
"""

import os
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 设置调试模式
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # 启动应用程序
    print("启动 Flask 应用程序...")
    print(f"监听地址: {app.config['HOST']}:{app.config['PORT']}")
    print(f"调试模式: {debug}")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=debug,
        use_reloader=True
    )