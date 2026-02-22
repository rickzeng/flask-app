#!/usr/bin/env python3
"""
Flask 主应用 - 集成股票数据模块
"""

from flask import Flask, jsonify, render_template_string
import logging
import os
from datetime import datetime

# 尝试导入股票API模块
try:
    from stock_api import register_stock_blueprint
    STOCK_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入股票模块: {e}")
    STOCK_MODULE_AVAILABLE = False

# 尝试导入 V2free 自动化模块
try:
    from v2free_routes import register_v2free_blueprint
    V2FREE_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入 V2free 自动化模块: {e}")
    V2FREE_AVAILABLE = False

# 尝试导入配置
try:
    from config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("警告: 无法导入配置模块，使用默认配置")


def create_app():
    """创建Flask应用"""
    # 检查股票模块是否可用
    stock_module_available = False
    try:
        from stock_api import register_stock_blueprint
        stock_module_available = True
    except ImportError as e:
        print(f"警告: 无法导入股票模块: {e}")
        stock_module_available = False
    
    # 检查 V2free 自动化模块是否可用
    v2free_available = False
    try:
        from v2free_routes import register_v2free_blueprint
        v2free_available = True
    except ImportError as e:
        print(f"警告: 无法导入 V2free 自动化模块: {e}")
        v2free_available = False
    
    app = Flask(__name__)
    
    # 基础配置
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        DEBUG=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true',
        HOST=os.environ.get('HOST', '0.0.0.0'),
        PORT=int(os.environ.get('PORT', 5000)),
        LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置日志
    setup_logging(app)
    
    # 注册路由
    register_routes(app, stock_module_available, v2free_available)
    
    # 注册股票API（如果可用）
    if stock_module_available:
        try:
            register_stock_blueprint(app)
            app.logger.info("股票数据API模块已成功注册")
        except Exception as e:
            app.logger.error(f"注册股票API模块失败: {e}")
            stock_module_available = False
    
    # 注册 V2free 自动化模块（如果可用）
    if v2free_available:
        try:
            register_v2free_blueprint(app)
            app.logger.info("V2free 自动化模块已成功注册")
        except Exception as e:
            app.logger.error(f"注册 V2free 自动化模块失败: {e}")
            v2free_available = False
    
    app.logger.info(f"Flask应用启动完成，股票模块: {'可用' if stock_module_available else '不可用'}，V2free模块: {'可用' if v2free_available else '不可用'}")
    return app


def setup_logging(app):
    """设置日志"""
    if not app.debug:
        # 生产环境：文件日志
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(os.path.join(log_dir, 'flask.log'))
        file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    else:
        # 开发环境：控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        console_handler.setLevel(logging.DEBUG)
        
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)


def register_routes(app, stock_module_available=False, V2FREE_AVAILABLE=False):
    """注册路由"""
    
    @app.route('/')
    def home():
        """首页"""
        stock_module_info = ""
        if stock_module_available:
            stock_module_info = """
            <h2>📈 股票数据模块</h2>
            <ul>
                <li><a href="/api/stock/health">/api/stock/health</a> - 股票模块健康检查</li>
                <li><a href="/api/stock/top_fund_flow?days=5&top_n=10">/api/stock/top_fund_flow</a> - 最近5天资金流入前10股票</li>
                <li><a href="/api/stock/details/000001">/api/stock/details/000001</a> - 股票详情示例</li>
                <li><a href="/api/stock/historical?code=000001">/api/stock/historical</a> - 历史数据</li>
                <li><a href="/api/stock/realtime?codes=000001,000002">/api/stock/realtime</a> - 实时数据</li>
                <li><a href="/api/stock/config">/api/stock/config</a> - 配置信息</li>
                <li><a href="/api/stock/docs">/api/stock/docs</a> - API文档</li>
            </ul>
            """
        else:
            stock_module_info = "<p>⚠️ 股票数据模块当前不可用</p>"
        
        v2free_module_info = ""
        try:
            from v2free_routes import V2FREE_AVAILABLE
            if V2FREE_AVAILABLE:
                v2free_module_info = """
                <h2>🌐 V2free 自动化模块</h2>
                <ul>
                    <li><a href="/v2free/">/v2free/</a> - V2free 管理页面</li>
                    <li><a href="/v2free/api/health">/v2free/api/health</a> - 健康检查</li>
                    <li><a href="/v2free/api/config">/v2free/api/config</a> - 配置信息</li>
                    <li><a href="/v2free/api/logs">/v2free/api/logs</a> - 访问日志</li>
                </ul>
                """
            else:
                v2free_module_info = "<p>⚠️ V2free 自动化模块当前不可用</p>"
        except:
            v2free_module_info = "<p>⚠️ V2free 自动化模块当前不可用</p>"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flask 应用程序</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ margin: 10px 0; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .module {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .status {{ padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .available {{ background: #d4edda; color: #155724; }}
                .unavailable {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <h1>🚀 Flask 应用程序</h1>
            <p>欢迎使用 Flask 应用程序！这是一个集成了股票数据功能的Web应用。</p>
            
            <div class="module">
                <h2>📊 核心功能</h2>
                <ul>
                    <li><a href="/api/hello">/api/hello</a> - 打招呼</li>
                    <li><a href="/api/health">/api/health</a> - 健康检查</li>
                </ul>
            </div>
            
            <div class="module">
                <h2>📈 股票数据模块
                    <span class="status {'available' if stock_module_available else 'unavailable'}">
                        {'✅ 可用' if stock_module_available else '❌ 不可用'}
                    </span>
                </h2>
                {stock_module_info}
            </div>
            
            <div class="module">
                <h2>🌐 V2free 自动化模块
                    <span class="status {'available' if V2FREE_AVAILABLE else 'unavailable'}">
                        {'✅ 可用' if V2FREE_AVAILABLE else '❌ 不可用'}
                    </span>
                </h2>
                {v2free_module_info}
            </div>
            
            <div class="module">
                <h2>🔧 系统信息</h2>
                <ul>
                    <li><strong>启动时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>调试模式:</strong> {'开启' if app.debug else '关闭'}</li>
                    <li><strong>主机:</strong> {app.config['HOST']}:{app.config['PORT']}</li>
                </ul>
            </div>
            
            <div class="module">
                <h2>📚 项目功能</h2>
                <ul>
                    <li>✅ Flask Web 应用框架</li>
                    <li>✅ A股股票数据获取</li>
                    <li>✅ 资金流向分析</li>
                    <li>✅ V2free 浏览器自动化（Playwright）</li>
                    <li>✅ RESTful API 接口</li>
                    <li>✅ 数据缓存机制</li>
                    <li>✅ 错误处理和日志</li>
                </ul>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_content)
    
    @app.route('/api/hello')
    def api_hello():
        """打招呼API"""
        return jsonify({
            'message': '你好！欢迎使用 Flask API',
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'flask_app': 'available',
                'stock_module': 'available' if stock_module_available else 'unavailable'
            }
        })
    
    @app.route('/api/health')
    def api_health():
        """健康检查API"""
        services = {
            'flask_app': 'healthy',
            'stock_module': 'healthy' if stock_module_available else 'unavailable'
        }
        
        # 检查股票模块健康
        if stock_module_available:
            try:
                from stock_api import get_stock_fetcher
                fetcher = get_stock_fetcher()
                # 简单测试
                test_stocks = fetcher.get_top_fund_flow_stocks(days=1, top_n=1)
                if test_stocks:
                    services['stock_module'] = 'healthy'
                else:
                    services['stock_module'] = 'degraded'
            except Exception as e:
                services['stock_module'] = f'unhealthy: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'service': 'flask-app',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'services': services
        })
    
    @app.route('/api/info')
    def api_info():
        """系统信息API"""
        return jsonify({
            'application': 'Flask Stock Data App',
            'version': '2.0.0',
            'description': '集成了A股股票数据获取功能的Flask应用',
            'timestamp': datetime.now().isoformat(),
            'modules': {
                'flask': 'available',
                'stock_data': 'available' if stock_module_available else 'unavailable',
                'v2free_automation': 'available' if V2FREE_AVAILABLE else 'unavailable',
                'reddit_push': 'available'  # 假设Reddit推送模块存在
            },
            'endpoints': {
                'core': ['/', '/api/hello', '/api/health', '/api/info'],
                'stock': [
                    '/api/stock/health',
                    '/api/stock/top_fund_flow',
                    '/api/stock/details/<code>',
                    '/api/stock/historical',
                    '/api/stock/realtime',
                    '/api/stock/config',
                    '/api/stock/docs'
                ] if stock_module_available else [],
                'v2free': [
                    '/v2free/',
                    '/v2free/api/health',
                    '/v2free/api/config',
                    '/v2free/api/logs',
                    '/v2free/api/login'
                ] if V2FREE_AVAILABLE else []
            }
        })


# 创建应用实例
app = create_app()

if __name__ == '__main__':
    app.logger.info(f"启动Flask应用，监听 {app.config['HOST']}:{app.config['PORT']}")
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )