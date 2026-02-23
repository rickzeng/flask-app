"""
A股股票数据获取模块
"""

import requests
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class StockDataProvider:
    """A股股票数据提供者"""
    
    def __init__(self):
        self.base_url = "http://push2.eastmoney.com/api/qt"
        self.cache = {}
        self.cache_expire_time = {}
        self.default_cache_timeout = 300  # 5分钟缓存
        
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        
        if key not in self.cache_expire_time:
            return False
            
        return time.time() < self.cache_expire_time[key]
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        if self._is_cache_valid(key):
            logger.debug(f"从缓存获取数据: {key}")
            return self.cache.get(key)
        return None
    
    def _set_cache(self, key: str, data: Dict, timeout: Optional[int] = None):
        """设置缓存"""
        self.cache[key] = data
        expire_time = timeout or self.default_cache_timeout
        self.cache_expire_time[key] = time.time() + expire_time
        logger.debug(f"数据已缓存: {key}, 过期时间: {expire_time}秒")
    
    def get_stock_basic_info(self, stock_code: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码，如 '000001' 或 '600000'
            
        Returns:
            包含股票基本信息的字典
        """
        cache_key = f"basic_{stock_code}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        try:
            # 处理股票代码格式
            market_prefix = '1' if stock_code.startswith('6') else '0'
            full_code = f"{market_prefix}.{stock_code}"
            
            url = f"{self.base_url}/stock/get"
            params = {
                'secid': full_code,
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data') is None:
                raise ValueError(f"无法获取股票 {stock_code} 的数据")
                
            result = {
                'code': stock_code,
                'name': data['data'].get('f58', ''),
                'price': data['data'].get('f2', 0) / 100 if data['data'].get('f2') else 0,
                'change': data['data'].get('f3', 0) / 100 if data['data'].get('f3') else 0,
                'change_percent': data['data'].get('f170', 0) / 100 if data['data'].get('f170') else 0,
                'volume': data['data'].get('f5', 0),
                'amount': data['data'].get('f6', 0) / 10000 if data['data'].get('f6') else 0,  # 万元
                'timestamp': datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 基本信息失败: {str(e)}")
            raise
    
    def get_stock_fund_flow(self, stock_code: str, days: int = 5) -> Dict:
        """
        获取股票资金流向数据
        
        Args:
            stock_code: 股票代码
            days: 获取最近几天的数据
            
        Returns:
            包含资金流向信息的字典
        """
        cache_key = f"flow_{stock_code}_{days}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        try:
            # 处理股票代码格式
            market_prefix = '1' if stock_code.startswith('6') else '0'
            full_code = f"{market_prefix}.{stock_code}"
            
            url = f"{self.base_url}/stock/fflow/kline/get"
            params = {
                'secid': full_code,
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
                'klt': '101',  # 日K
                'lmt': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('data') or not data['data'].get('klines'):
                raise ValueError(f"无法获取股票 {stock_code} 的资金流向数据")
                
            klines = data['data']['klines']
            result = {
                'code': stock_code,
                'fund_flows': [],
                'timestamp': datetime.now().isoformat()
            }
            
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 7:
                    result['fund_flows'].append({
                        'date': parts[0],
                        'main_flow': float(parts[1]) / 10000,  # 万元
                        'super_large_flow': float(parts[2]) / 10000,
                        'large_flow': float(parts[3]) / 10000,
                        'medium_flow': float(parts[4]) / 10000,
                        'small_flow': float(parts[5]) / 10000
                    })
            
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 资金流向数据失败: {str(e)}")
            raise
    
    def get_top_fund_flow_stocks(self, days: int = 5, limit: int = 10) -> List[Dict]:
        """
        获取最近几天资金流入前N的股票
        
        Args:
            days: 统计天数
            limit: 返回股票数量
            
        Returns:
            股票列表，按资金流入量排序
        """
        cache_key = f"top_fund_flow_{days}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        try:
            # 获取A股股票列表（前100只活跃股票）
            url = f"{self.base_url}/clist/get"
            params = {
                'pn': '1',
                'pz': '100',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('data') or not data['data'].get('diff'):
                raise ValueError("无法获取股票列表")
                
            stocks = []
            for item in data['data']['diff'][:50]:  # 只取前50只进行分析
                stock_code = item.get('f12', '')
                if not stock_code:
                    continue
                    
                try:
                    fund_flow_data = self.get_stock_fund_flow(stock_code, days)
                    main_flow_total = sum(flow['main_flow'] for flow in fund_flow_data['fund_flows'])
                    
                    stocks.append({
                        'code': stock_code,
                        'name': item.get('f14', ''),
                        'price': item.get('f2', 0) / 100 if item.get('f2') else 0,
                        'change': item.get('f3', 0) / 100 if item.get('f3') else 0,
                        'change_percent': item.get('f170', 0) / 100 if item.get('f170') else 0,
                        'total_main_flow': main_flow_total,  # 总主力资金流入
                        'days': days,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 时出错: {str(e)}")
                    continue
            
            # 按主力资金流入量排序
            stocks.sort(key=lambda x: x['total_main_flow'], reverse=True)
            
            result = stocks[:limit]
            self._set_cache(cache_key, result, timeout=600)  # 缓存10分钟
            
            return result
            
        except Exception as e:
            logger.error(f"获取资金流入前{limit}名股票失败: {str(e)}")
            raise
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_expire_time.clear()
        logger.info("股票数据缓存已清空")