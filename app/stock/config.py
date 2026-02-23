#!/usr/bin/env python3
"""
A股股票数据配置模块
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# 项目根目录
BASE_DIR = Path(__file__).parent

# 股票数据配置
STOCK_CONFIG = {
    # 数据源配置
    'data_sources': {
        'eastmoney': {
            'base_url': 'http://quote.eastmoney.com',
            'api_url': 'http://push2.eastmoney.com/api',
            'timeout': 30,
            'retry_times': 3
        },
        'sina': {
            'base_url': 'http://hq.sinajs.cn',
            'timeout': 20,
            'retry_times': 2
        },
        'tencent': {
            'base_url': 'http://qt.gtimg.cn',
            'timeout': 20,
            'retry_times': 2
        }
    },
    
    # 数据获取配置
    'data_fetch': {
        'days_back': 5,  # 获取最近几天的数据
        'top_n': 10,     # 获取前N名
        'cache_hours': 1,  # 缓存小时数
        'update_interval': 30,  # 更新间隔（分钟）
    },
    
    # 股票筛选条件
    'filter_criteria': {
        'min_market_cap': 0,             # 最小市值（0表示不限制）
        'max_pe_ratio': 200,             # 最大市盈率
        'min_turnover_rate': 0,          # 最小换手率（%）
        'exclude_st': False,             # 排除ST股票（测试时设为False）
        'exclude_suspended': False,      # 排除停牌股票（测试时设为False）
    },
    
    # 资金流向指标权重
    'fund_flow_weights': {
        'main_net_inflow': 0.4,      # 主力净流入权重
        'large_order_inflow': 0.3,   # 大单净流入权重
        'medium_order_inflow': 0.2,  # 中单净流入权重
        'small_order_inflow': 0.1,   # 小单净流入权重
    },
    
    # 文件存储配置
    'storage': {
        'data_dir': BASE_DIR / 'stock_data' / 'data',
        'cache_dir': BASE_DIR / 'stock_data' / 'cache',
        'log_dir': BASE_DIR / 'stock_data' / 'logs',
        'output_dir': BASE_DIR / 'stock_data' / 'output',
    },
    
    # 日志配置
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': BASE_DIR / 'stock_data' / 'logs' / 'stock_data.log',
        'max_size_mb': 10,
        'backup_count': 5
    },
    
    # API配置
    'api': {
        'endpoints': {
            'top_fund_flow': '/api/stock/top_fund_flow',
            'stock_details': '/api/stock/details',
            'historical_data': '/api/stock/historical',
            'realtime_data': '/api/stock/realtime',
        },
        'rate_limit': {
            'requests_per_minute': 60,
            'requests_per_hour': 300
        }
    }
}


def get_config():
    """获取配置"""
    return STOCK_CONFIG.copy()


def get_data_source_config(source_name='eastmoney'):
    """获取指定数据源配置"""
    config = STOCK_CONFIG.copy()
    if source_name in config['data_sources']:
        return config['data_sources'][source_name]
    return config['data_sources']['eastmoney']


def get_storage_paths():
    """获取存储路径"""
    config = STOCK_CONFIG.copy()
    storage = config['storage']
    
    # 确保目录存在
    for key, path in storage.items():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
    
    return storage


def get_date_range(days_back=5):
    """获取日期范围"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'days': days_back
    }


def validate_config():
    """验证配置"""
    config = STOCK_CONFIG.copy()
    
    # 验证数据源配置
    for source_name, source_config in config['data_sources'].items():
        if 'base_url' not in source_config:
            raise ValueError(f"数据源 {source_name} 缺少 base_url 配置")
    
    # 验证存储目录
    storage_paths = get_storage_paths()
    for path_name, path in storage_paths.items():
        if not isinstance(path, Path):
            raise ValueError(f"存储路径 {path_name} 必须是 Path 对象")
    
    return True


if __name__ == '__main__':
    # 测试配置
    try:
        validate_config()
        print("配置验证通过")
        
        # 显示配置信息
        config = get_config()
        print(f"数据源: {list(config['data_sources'].keys())}")
        print(f"获取天数: {config['data_fetch']['days_back']}")
        print(f"前N名: {config['data_fetch']['top_n']}")
        
        date_range = get_date_range()
        print(f"日期范围: {date_range['start_date']} 到 {date_range['end_date']}")
        
    except Exception as e:
        print(f"配置验证失败: {e}")