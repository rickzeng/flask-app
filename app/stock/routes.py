"""
股票数据API路由
"""

from flask import Blueprint, jsonify, request, current_app
from app.stock_service import StockDataProvider
import logging
from datetime import datetime

# 创建蓝图
stock_bp = Blueprint('stock', __name__, url_prefix='/api/stocks')
logger = logging.getLogger(__name__)

# 获取股票数据提供者实例
stock_provider = StockDataProvider()


@stock_bp.route('/health', methods=['GET'])
def health_check():
    """股票模块健康检查"""
    return jsonify({
        'status': 'healthy',
        'module': 'stock_data',
        'timestamp': datetime.now().isoformat()
    })


@stock_bp.route('/info/<string:stock_code>', methods=['GET'])
def get_stock_info(stock_code):
    """
    获取股票基本信息
    
    Args:
        stock_code: 股票代码
        
    Returns:
        JSON格式的股票信息
    """
    try:
        # 验证股票代码格式
        if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
            return jsonify({
                'status': 'error',
                'message': '股票代码格式错误，请使用6位数字代码'
            }), 400
        
        stock_info = stock_provider.get_stock_basic_info(stock_code)
        
        return jsonify({
            'status': 'success',
            'data': stock_info
        })
        
    except ValueError as e:
        logger.warning(f"获取股票信息失败 - 股票代码: {stock_code}, 错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"获取股票信息时发生未知错误 - 股票代码: {stock_code}, 错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '服务器内部错误，请稍后重试'
        }), 500


@stock_bp.route('/flow/<string:stock_code>', methods=['GET'])
def get_stock_fund_flow(stock_code):
    """
    获取股票资金流向数据
    
    Args:
        stock_code: 股票代码
        
    Returns:
        JSON格式的资金流向数据
    """
    try:
        # 验证股票代码格式
        if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
            return jsonify({
                'status': 'error',
                'message': '股票代码格式错误，请使用6位数字代码'
            }), 400
        
        # 获取天数参数，默认为5天
        days = request.args.get('days', 5, type=int)
        if days <= 0 or days > 30:
            return jsonify({
                'status': 'error',
                'message': '天数参数必须在1-30之间'
            }), 400
        
        fund_flow_data = stock_provider.get_stock_fund_flow(stock_code, days)
        
        return jsonify({
            'status': 'success',
            'data': fund_flow_data
        })
        
    except ValueError as e:
        logger.warning(f"获取资金流向失败 - 股票代码: {stock_code}, 错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"获取资金流向时发生未知错误 - 股票代码: {stock_code}, 错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '服务器内部错误，请稍后重试'
        }), 500


@stock_bp.route('/top-fund-flow', methods=['GET'])
def get_top_fund_flow_stocks():
    """
    获取资金流入前N的股票
    
    Returns:
        JSON格式的热门股票列表
    """
    try:
        # 获取天数和限制数量参数
        days = request.args.get('days', 5, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 验证参数
        if days <= 0 or days > 30:
            return jsonify({
                'status': 'error',
                'message': '天数参数必须在1-30之间'
            }), 400
            
        if limit <= 0 or limit > 50:
            return jsonify({
                'status': 'error',
                'message': '股票数量限制必须在1-50之间'
            }), 400
        
        top_stocks = stock_provider.get_top_fund_flow_stocks(days, limit)
        
        return jsonify({
            'status': 'success',
            'data': {
                'stocks': top_stocks,
                'days': days,
                'limit': limit,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        logger.warning(f"获取热门股票失败, 错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"获取热门股票时发生未知错误, 错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '服务器内部错误，请稍后重试'
        }), 500


@stock_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """清空股票数据缓存"""
    try:
        stock_provider.clear_cache()
        logger.info("用户手动清空了股票数据缓存")
        
        return jsonify({
            'status': 'success',
            'message': '缓存已清空'
        })
        
    except Exception as e:
        logger.error(f"清空缓存时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '清空缓存失败'
        }), 500