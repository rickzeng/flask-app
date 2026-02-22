#!/usr/bin/env python3
"""
A股股票数据API模块（混合数据源版本）
"""

from flask import Blueprint, jsonify, request, current_app, render_template
from datetime import datetime, timedelta
import json
from pathlib import Path

# 使用混合数据获取器
from stock_data_fetcher_hybrid_v2 import StockDataFetcherHybrid
from stock_config import get_config, get_date_range

# 创建蓝图
stock_bp = Blueprint('stock', __name__, url_prefix='/api/stock')

# 全局股票数据获取器实例
_stock_fetcher = None

def get_stock_fetcher():
    """获取股票数据获取器实例（单例模式）"""
    global _stock_fetcher
    if _stock_fetcher is None:
        _stock_fetcher = StockDataFetcherHybrid(
            real_time_source='tencent',
            history_source='baostock',
            use_cache=True
        )
    return _stock_fetcher


@stock_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'stock-data-api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'data_source': 'mixed (tencent + baostock)'
    })


@stock_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """股票分析页面"""
    return render_template('stock_dashboard.html')


@stock_bp.route('/top_fund_flow', methods=['GET'])
def get_top_fund_flow():
    """
    获取最近几天资金流入前N的股票

    Query Parameters:
        days: 最近几天（默认5）
        top_n: 前N名（默认10）
        format: 返回格式（json/csv，默认json）
        include_details: 是否包含详细信息（true/false，默认false）
    """
    try:
        # 获取查询参数
        days = request.args.get('days', default=5, type=int)
        top_n = request.args.get('top_n', default=10, type=int)
        output_format = request.args.get('format', default='json', type=str)
        include_details = request.args.get('include_details', default='false', type=str).lower() == 'true'

        # 参数验证
        if days < 1 or days > 30:
            return jsonify({
                'error': '参数错误',
                'message': 'days 参数必须在 1-30 之间'
            }), 400

        if top_n < 1 or top_n > 50:
            return jsonify({
                'error': '参数错误',
                'message': 'top_n 参数必须在 1-50 之间'
            }), 400

        # 获取股票数据
        fetcher = get_stock_fetcher()
        stocks = fetcher.get_top_fund_flow_stocks(days=days, top_n=top_n)

        if include_details:
            # 获取每只股票的详细信息
            for stock in stocks:
                details = fetcher.get_stock_details(stock['code'])
                if details:
                    stock['details'] = details

        # 准备响应数据
        date_range = get_date_range(days)
        response_data = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'days': days,
                'top_n': top_n,
                'date_range': date_range,
                'data_source': 'mixed (tencent + baostock)'
            },
            'count': len(stocks),
            'data': stocks
        }

        # 根据格式返回
        if output_format.lower() == 'csv':
            # 转换为CSV格式
            import pandas as pd

            # 简化数据用于CSV
            simplified_data = []
            for stock in stocks:
                simplified = {
                    'rank': stock.get('rank', ''),
                    'code': stock.get('code', ''),
                    'name': stock.get('name', ''),
                    'market': stock.get('market', ''),
                    'current_price': stock.get('current_price', ''),
                    'change_percent': stock.get('change_percent', ''),
                    'fund_flow_score': stock.get('fund_flow_score', ''),
                    'total_inflow': stock.get('fund_flow', {}).get('total_inflow', ''),
                    'analysis': stock.get('analysis', ''),
                    'update_time': stock.get('update_time', '')
                }
                simplified_data.append(simplified)

            csv_df = pd.DataFrame(simplified_data)
            csv_content = csv_df.to_csv(index=False, encoding='utf-8-sig')

            return current_app.response_class(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment;filename=top_stocks_{datetime.now().strftime("%Y%m%d")}.csv'}
            )

        # 默认返回JSON
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"获取股票数据失败: {e}")
        return jsonify({
            'error': '服务器错误',
            'message': str(e)
        }), 500


@stock_bp.route('/details/<stock_code>', methods=['GET'])
def get_stock_details(stock_code):
    """
    获取股票详细信息

    Path Parameters:
        stock_code: 股票代码（如 000001）
    """
    try:
        # 验证股票代码格式
        if not stock_code or len(stock_code) != 6:
            return jsonify({
                'error': '参数错误',
                'message': '股票代码必须是6位数字'
            }), 400

        # 获取股票详情
        fetcher = get_stock_fetcher()
        details = fetcher.get_stock_details(stock_code)

        if not details:
            return jsonify({
                'error': '未找到数据',
                'message': f'未找到股票 {stock_code} 的详细信息'
            }), 404

        # 准备响应数据
        response_data = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'stock_code': stock_code,
            'data': details
        }

        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"获取股票详情失败: {e}")
        return jsonify({
            'error': '服务器错误',
            'message': str(e)
        }), 500


def register_stock_blueprint(app):
    """注册股票API蓝图到Flask应用"""
    app.register_blueprint(stock_bp)
    app.logger.info("股票数据API已注册（混合数据源：tencent + baostock）")

    # 添加API文档路由
    @app.route('/api/stock/docs')
    def stock_api_docs():
        """股票API文档"""
        docs = {
            'endpoints': {
                '/api/stock/health': {
                    'method': 'GET',
                    'description': '健康检查',
                    'parameters': None
                },
                '/api/stock/dashboard': {
                    'method': 'GET',
                    'description': '股票分析页面',
                    'parameters': None
                },
                '/api/stock/top_fund_flow': {
                    'method': 'GET',
                    'description': '获取资金流入前N的股票',
                    'parameters': {
                        'days': '最近几天（默认5）',
                        'top_n': '前N名（默认10）',
                        'format': '返回格式（json/csv）',
                        'include_details': '是否包含详细信息'
                    }
                },
                '/api/stock/details/<code>': {
                    'method': 'GET',
                    'description': '获取股票详细信息',
                    'parameters': {
                        'code': '股票代码（路径参数）'
                    }
                }
            },
            'data_sources': {
                'real_time': 'tencent (腾讯财经）',
                'history': 'baostock (Baostock)',
                'notes': '实时数据来自腾讯财经，历史数据来自Baostock'
            }
        }

        return jsonify(docs)


if __name__ == '__main__':
    # 测试API
    from flask import Flask

    app = Flask(__name__)
    register_stock_blueprint(app)

    print("股票API测试服务器启动...")
    print("可用端点:")
    print("  GET /api/stock/health - 健康检查")
    print("  GET /api/stock/dashboard - 股票分析页面")
    print("  GET /api/stock/top_fund_flow - 资金流入前N股票")
    print("  GET /api/stock/details/<code> - 股票详情")
    print("  GET /api/stock/docs - API文档")
