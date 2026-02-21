#!/usr/bin/env python3
"""
A股股票数据API模块
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import json
from pathlib import Path

from stock_data_fetcher import StockDataFetcher
from stock_config import get_config, get_date_range

# 创建蓝图
stock_bp = Blueprint('stock', __name__, url_prefix='/api/stock')

# 全局股票数据获取器实例
_stock_fetcher = None

def get_stock_fetcher():
    """获取股票数据获取器实例（单例模式）"""
    global _stock_fetcher
    if _stock_fetcher is None:
        _stock_fetcher = StockDataFetcher(data_source='eastmoney', use_cache=True)
    return _stock_fetcher


@stock_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'stock-data-api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


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
                'date_range': date_range
            },
            'count': len(stocks),
            'data': stocks
        }
        
        # 根据格式返回
        if output_format.lower() == 'csv':
            # 转换为CSV格式
            import pandas as pd
            df = pd.DataFrame(stocks)
            
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
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'stock_code': stock_code,
            'data': details
        })
        
    except Exception as e:
        current_app.logger.error(f"获取股票详情失败: {e}")
        return jsonify({
            'error': '服务器错误',
            'message': str(e)
        }), 500


@stock_bp.route('/historical', methods=['GET'])
def get_historical_data():
    """
    获取股票历史数据
    
    Query Parameters:
        code: 股票代码（必需）
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        period: 周期（day/week/month，默认day）
    """
    try:
        stock_code = request.args.get('code', type=str)
        
        if not stock_code:
            return jsonify({
                'error': '参数错误',
                'message': '必须提供股票代码（code）参数'
            }), 400
        
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        period = request.args.get('period', default='day', type=str)
        
        # 生成模拟历史数据
        import numpy as np
        from datetime import datetime, timedelta
        
        # 如果没有提供日期，使用最近30天
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 解析日期
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 生成日期序列
        dates = []
        current_dt = start_dt
        while current_dt <= end_dt:
            dates.append(current_dt.strftime('%Y-%m-%d'))
            if period == 'day':
                current_dt += timedelta(days=1)
            elif period == 'week':
                current_dt += timedelta(weeks=1)
            elif period == 'month':
                # 简单月份增加
                year = current_dt.year
                month = current_dt.month + 1
                if month > 12:
                    month = 1
                    year += 1
                current_dt = current_dt.replace(year=year, month=month)
            else:
                current_dt += timedelta(days=1)
        
        # 生成模拟价格数据
        base_price = np.random.uniform(10, 100)
        historical_data = []
        
        for i, date in enumerate(dates):
            # 随机波动
            change = np.random.normal(0, 0.02)  # 2%的标准差
            price = base_price * (1 + change)
            
            # 生成OHLC数据
            open_price = price * (1 + np.random.uniform(-0.01, 0.01))
            high_price = max(open_price, price) * (1 + np.random.uniform(0, 0.02))
            low_price = min(open_price, price) * (1 - np.random.uniform(0, 0.02))
            close_price = price
            
            volume = np.random.uniform(100000, 1000000)
            
            historical_data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': int(volume),
                'change': round(close_price - open_price, 2),
                'change_percent': round((close_price - open_price) / open_price * 100, 2)
            })
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'code': stock_code,
                'start_date': start_date,
                'end_date': end_date,
                'period': period
            },
            'count': len(historical_data),
            'data': historical_data
        })
        
    except ValueError as e:
        return jsonify({
            'error': '参数错误',
            'message': f'日期格式错误: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f"获取历史数据失败: {e}")
        return jsonify({
            'error': '服务器错误',
            'message': str(e)
        }), 500


@stock_bp.route('/realtime', methods=['GET'])
def get_realtime_data():
    """
    获取股票实时数据
    
    Query Parameters:
        codes: 股票代码列表，用逗号分隔（如 000001,000002）
    """
    try:
        codes_param = request.args.get('codes', type=str)
        
        if not codes_param:
            return jsonify({
                'error': '参数错误',
                'message': '必须提供股票代码（codes）参数'
            }), 400
        
        codes = [code.strip() for code in codes_param.split(',') if code.strip()]
        
        if len(codes) > 20:
            return jsonify({
                'error': '参数错误',
                'message': '一次最多查询20只股票'
            }), 400
        
        # 生成模拟实时数据
        import numpy as np
        realtime_data = []
        
        for code in codes:
            # 基础价格
            base_price = np.random.uniform(10, 200)
            
            # 随机变化
            change_percent = np.random.uniform(-5, 5)
            current_price = base_price * (1 + change_percent / 100)
            
            # 买卖盘数据
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []
            
            for i in range(5):
                bid_prices.append(round(current_price * (1 - (i+1) * 0.001), 2))
                bid_volumes.append(int(np.random.uniform(100, 1000)))
                
                ask_prices.append(round(current_price * (1 + (i+1) * 0.001), 2))
                ask_volumes.append(int(np.random.uniform(100, 1000)))
            
            stock_data = {
                'code': code,
                'name': f"股票{code}",
                'current_price': round(current_price, 2),
                'change': round(current_price - base_price, 2),
                'change_percent': round(change_percent, 2),
                'volume': int(np.random.uniform(100000, 1000000)),
                'amount': int(np.random.uniform(10000000, 100000000)),
                'bid_prices': bid_prices,
                'bid_volumes': bid_volumes,
                'ask_prices': ask_prices,
                'ask_volumes': ask_volumes,
                'timestamp': datetime.now().isoformat(),
                'update_time': datetime.now().strftime('%H:%M:%S')
            }
            
            realtime_data.append(stock_data)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'count': len(realtime_data),
            'data': realtime_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取实时数据失败: {e}")
        return jsonify({
            'error': '服务器错误',
            'message': str(e)
        }), 500


@stock_bp.route('/config', methods=['GET'])
def get_config_info():
    """获取配置信息"""
    try:
        config = get_config()
        
        # 移除敏感信息
        safe_config = config.copy()
        if 'data_sources' in safe_config:
            for source in safe_config['data_sources'].values():
                if 'api_key' in source:
                    del source['api_key']
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'config': safe_config
        })
        
    except Exception as e:
        current_app.logger.error(f"获取配置失败: {e}")
        return jsonify({
            'error': '服务器错误',
            'message': str(e)
        }), 500


def register_stock_blueprint(app):
    """注册股票API蓝图到Flask应用"""
    app.register_blueprint(stock_bp)
    app.logger.info("股票数据API已注册")
    
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
                },
                '/api/stock/historical': {
                    'method': 'GET',
                    'description': '获取股票历史数据',
                    'parameters': {
                        'code': '股票代码',
                        'start_date': '开始日期',
                        'end_date': '结束日期',
                        'period': '周期（day/week/month）'
                    }
                },
                '/api/stock/realtime': {
                    'method': 'GET',
                    'description': '获取股票实时数据',
                    'parameters': {
                        'codes': '股票代码列表（逗号分隔）'
                    }
                },
                '/api/stock/config': {
                    'method': 'GET',
                    'description': '获取配置信息',
                    'parameters': None
                }
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
    print("  GET /api/stock/top_fund_flow - 资金流入前N股票")
    print("  GET /api/stock/details/<code> - 股票详情")
    print("  GET /api/stock/historical - 历史数据")
    print("  GET /api/stock/realtime - 实时数据")
    print("  GET /api/stock/config - 配置信息")
    print("  GET /api/stock/docs - API文档")