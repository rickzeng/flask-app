from flask import Flask, jsonify
from config import get_config
import logging
import os

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(get_config(config_name))
    
    # 配置日志
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/flask.log')
        file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask应用启动')
    
    # 注册蓝图
    from app.stock_routes import stock_bp
    app.register_blueprint(stock_bp)
    
    # 注册路由
    register_routes(app)
    
    return app

def register_routes(app):
    """注册路由"""
    
    @app.route('/')
    def home():
        return '''
        <h1>Flask 应用程序</h1>
        <p>欢迎使用 Flask 应用程序！</p>
        <ul>
            <li><a href="/api/hello">/api/hello</a> - 打招呼</li>
            <li><a href="/api/health">/api/health</a> - 健康检查</li>
            <li><a href="/api/stocks/health">/api/stocks/health</a> - 股票模块健康检查</li>
            <li><a href="/api/stocks/top-fund-flow?days=5&limit=10">/api/stocks/top-fund-flow</a> - 资金流入前10股票</li>
        </ul>
        '''

    @app.route('/api/hello')
    def api_hello():
        return jsonify({
            'message': '你好！欢迎使用 Flask API',
            'status': 'success',
            'timestamp': '2024-02-17T09:45:00Z'
        })

    @app.route('/api/health')
    def api_health():
        return jsonify({
            'status': 'healthy',
            'service': 'flask-app',
            'version': '1.0.0'
        })

# 创建应用实例（用于直接运行）
app = create_app()

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])