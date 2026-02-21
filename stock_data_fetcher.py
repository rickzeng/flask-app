#!/usr/bin/env python3
"""
A股股票数据获取模块
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from stock_config import get_config, get_storage_paths, get_date_range


class StockDataFetcher:
    """A股股票数据获取器"""
    
    def __init__(self, data_source='eastmoney', use_cache=True):
        """
        初始化股票数据获取器
        
        Args:
            data_source: 数据源名称 ('eastmoney', 'sina', 'tencent')
            use_cache: 是否使用缓存
        """
        self.config = get_config()
        self.data_source = data_source
        self.use_cache = use_cache
        
        # 获取数据源配置
        self.source_config = self.config['data_sources'].get(
            data_source, 
            self.config['data_sources']['eastmoney']
        )
        
        # 获取存储路径
        self.storage_paths = get_storage_paths()
        
        # 设置日志
        self._setup_logging()
        
        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'http://quote.eastmoney.com/'
        })
        
        self.logger.info(f"StockDataFetcher 初始化完成，数据源: {data_source}")
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config['logging']
        self.logger = logging.getLogger('stock_data_fetcher')
        
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_config['level'])
            console_formatter = logging.Formatter(log_config['format'])
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # 文件处理器
            log_file = log_config['file']
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_config['level'])
            file_formatter = logging.Formatter(log_config['format'])
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            self.logger.setLevel(log_config['level'])
    
    def _get_cache_key(self, function_name: str, params: Dict) -> str:
        """生成缓存键"""
        import hashlib
        param_str = json.dumps(params, sort_keys=True)
        key = f"{function_name}_{hashlib.md5(param_str.encode()).hexdigest()}"
        return key
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        cache_dir = self.storage_paths['cache_dir']
        return cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存加载数据"""
        if not self.use_cache:
            return None
        
        cache_file = self._get_cache_file(cache_key)
        if cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            cache_hours = self.config['data_fetch']['cache_hours']
            
            if cache_age < cache_hours * 3600:  # 缓存未过期
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.logger.debug(f"从缓存加载数据: {cache_key}")
                    return data
                except Exception as e:
                    self.logger.warning(f"加载缓存失败: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Any):
        """保存数据到缓存"""
        if not self.use_cache:
            return
        
        try:
            cache_file = self._get_cache_file(cache_key)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"数据已缓存: {cache_key}")
        except Exception as e:
            self.logger.warning(f"保存缓存失败: {e}")
    
    def _make_request(self, url: str, params: Dict = None, method='GET') -> Optional[Dict]:
        """发送HTTP请求"""
        try:
            if method.upper() == 'GET':
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.source_config['timeout']
                )
            else:
                response = self.session.post(
                    url, 
                    data=params, 
                    timeout=self.source_config['timeout']
                )
            
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                return response.json()
            except:
                # 如果不是JSON，返回文本
                return {'text': response.text}
                
        except requests.exceptions.Timeout:
            self.logger.error(f"请求超时: {url}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {e}")
        
        return None
    
    def get_top_fund_flow_stocks(self, days: int = 5, top_n: int = 10) -> List[Dict]:
        """
        获取最近几天资金流入前N的股票
        
        Args:
            days: 最近几天
            top_n: 前N名
            
        Returns:
            股票数据列表
        """
        self.logger.info(f"开始获取最近{days}天资金流入前{top_n}的股票")
        
        # 生成缓存键
        cache_key = self._get_cache_key('top_fund_flow', {'days': days, 'top_n': top_n})
        
        # 尝试从缓存加载
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # 根据数据源选择不同的获取方法
            if self.data_source == 'eastmoney':
                stocks = self._get_from_eastmoney(days, top_n)
            elif self.data_source == 'sina':
                stocks = self._get_from_sina(days, top_n)
            elif self.data_source == 'tencent':
                stocks = self._get_from_tencent(days, top_n)
            else:
                stocks = self._get_from_eastmoney(days, top_n)
            
            # 过滤和排序
            filtered_stocks = self._filter_stocks(stocks)
            sorted_stocks = self._sort_by_fund_flow(filtered_stocks)
            top_stocks = sorted_stocks[:top_n]
            
            # 添加额外信息
            enriched_stocks = self._enrich_stock_data(top_stocks)
            
            # 保存到缓存
            self._save_to_cache(cache_key, enriched_stocks)
            
            self.logger.info(f"成功获取 {len(enriched_stocks)} 只股票数据")
            return enriched_stocks
            
        except Exception as e:
            self.logger.error(f"获取股票数据失败: {e}")
            return []
    
    def _get_from_eastmoney(self, days: int, top_n: int) -> List[Dict]:
        """从东方财富获取数据"""
        base_url = self.source_config['base_url']
        
        # 模拟数据（实际需要调用真实API）
        # 这里使用模拟数据作为示例
        mock_stocks = []
        
        # 生成模拟股票数据
        stock_codes = ['000001', '000002', '000858', '600519', '000333', 
                      '002415', '300750', '601318', '600036', '000651']
        
        stock_names = ['平安银行', '万科A', '五粮液', '贵州茅台', '美的集团',
                      '海康威视', '宁德时代', '中国平安', '招商银行', '格力电器']
        
        for i in range(len(stock_codes)):
            # 生成模拟资金流向数据
            fund_flow = {
                'main_net_inflow': np.random.uniform(1000, 10000),  # 主力净流入（万元）
                'large_order_inflow': np.random.uniform(500, 5000),
                'medium_order_inflow': np.random.uniform(200, 2000),
                'small_order_inflow': np.random.uniform(100, 1000),
                'total_inflow': np.random.uniform(2000, 20000),
            }
            
            # 计算综合得分
            weights = self.config['fund_flow_weights']
            score = (
                fund_flow['main_net_inflow'] * weights['main_net_inflow'] +
                fund_flow['large_order_inflow'] * weights['large_order_inflow'] +
                fund_flow['medium_order_inflow'] * weights['medium_order_inflow'] +
                fund_flow['small_order_inflow'] * weights['small_order_inflow']
            )
            
            stock = {
                'code': stock_codes[i],
                'name': stock_names[i],
                'market': 'SZ' if stock_codes[i].startswith('00') or stock_codes[i].startswith('30') else 'SH',
                'current_price': np.random.uniform(10, 200),
                'change_percent': np.random.uniform(-5, 5),
                'volume': np.random.uniform(100000, 1000000),
                'turnover_rate': np.random.uniform(0.5, 5),
                'market_cap': np.random.uniform(1000000, 10000000),
                'pe_ratio': np.random.uniform(10, 50),
                'fund_flow': fund_flow,
                'fund_flow_score': round(score, 2),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            mock_stocks.append(stock)
        
        self.logger.info(f"从东方财富获取到 {len(mock_stocks)} 只股票模拟数据")
        return mock_stocks
    
    def _get_from_sina(self, days: int, top_n: int) -> List[Dict]:
        """从新浪财经获取数据（模拟）"""
        self.logger.info("使用新浪财经数据源（模拟）")
        return self._get_from_eastmoney(days, top_n)
    
    def _get_from_tencent(self, days: int, top_n: int) -> List[Dict]:
        """从腾讯财经获取数据（模拟）"""
        self.logger.info("使用腾讯财经数据源（模拟）")
        return self._get_from_eastmoney(days, top_n)
    
    def _filter_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """过滤股票"""
        criteria = self.config['filter_criteria']
        filtered_stocks = []
        
        for stock in stocks:
            # 排除ST股票
            if criteria['exclude_st'] and ('ST' in stock.get('name', '') or '*ST' in stock.get('name', '')):
                continue
            
            # 检查市值
            if stock.get('market_cap', 0) < criteria['min_market_cap']:
                continue
            
            # 检查市盈率
            if stock.get('pe_ratio', 0) > criteria['max_pe_ratio']:
                continue
            
            # 检查换手率
            if stock.get('turnover_rate', 0) < criteria['min_turnover_rate']:
                continue
            
            filtered_stocks.append(stock)
        
        self.logger.info(f"过滤后剩余 {len(filtered_stocks)} 只股票")
        return filtered_stocks
    
    def _sort_by_fund_flow(self, stocks: List[Dict]) -> List[Dict]:
        """按资金流向排序"""
        return sorted(
            stocks, 
            key=lambda x: x.get('fund_flow_score', 0), 
            reverse=True
        )
    
    def _enrich_stock_data(self, stocks: List[Dict]) -> List[Dict]:
        """丰富股票数据"""
        for stock in stocks:
            # 添加排名
            stock['rank'] = stocks.index(stock) + 1
            
            # 添加分析建议
            score = stock.get('fund_flow_score', 0)
            if score > 5000:
                stock['analysis'] = '资金大幅流入，关注度高'
                stock['recommendation'] = '积极关注'
            elif score > 2000:
                stock['analysis'] = '资金明显流入，表现活跃'
                stock['recommendation'] = '适度关注'
            else:
                stock['analysis'] = '资金流入一般，需观察'
                stock['recommendation'] = '谨慎关注'
            
            # 添加技术指标（模拟）
            stock['technical_indicators'] = {
                'rsi': round(np.random.uniform(30, 70), 2),
                'macd': round(np.random.uniform(-2, 2), 2),
                'bollinger_position': round(np.random.uniform(0, 100), 2),
                'volume_ratio': round(np.random.uniform(0.5, 2), 2)
            }
        
        return stocks
    
    def save_to_file(self, stocks: List[Dict], filename: str = None):
        """保存股票数据到文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"top_stocks_{timestamp}.json"
        
        output_dir = self.storage_paths['output_dir']
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'count': len(stocks),
                    'data': stocks
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"股票数据已保存到: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存文件失败: {e}")
            return None
    
    def get_stock_details(self, stock_code: str) -> Optional[Dict]:
        """获取股票详细信息"""
        cache_key = self._get_cache_key('stock_details', {'code': stock_code})
        
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # 模拟股票详情数据
        details = {
            'code': stock_code,
            'name': f"股票{stock_code}",
            'company_name': f"{stock_code}股份有限公司",
            'industry': np.random.choice(['金融', '科技', '消费', '医药', '制造']),
            'concept': np.random.choice(['人工智能', '新能源', '5G', '芯片', '生物医药'], 3),
            'listing_date': '2010-01-01',
            'total_shares': np.random.uniform(100000, 1000000),
            'circulating_shares': np.random.uniform(50000, 500000),
            'recent_news': [
                {'title': '公司发布年度报告', 'date': '2024-03-15', 'source': '证券时报'},
                {'title': '重大项目签约', 'date': '2024-03-10', 'source': '上海证券报'},
            ],
            'financial_indicators': {
                'revenue_growth': round(np.random.uniform(-10, 30), 2),
                'profit_growth': round(np.random.uniform(-20, 40), 2),
                'roe': round(np.random.uniform(5, 20), 2),
                'debt_ratio': round(np.random.uniform(20, 60), 2),
            }
        }
        
        self._save_to_cache(cache_key, details)
        return details


if __name__ == '__main__':
    # 测试股票数据获取器
    fetcher = StockDataFetcher(data_source='eastmoney', use_cache=True)
    
    # 获取最近5天资金流入前10的股票
    top_stocks = fetcher.get_top_fund_flow_stocks(days=5, top_n=10)
    
    print(f"获取到 {len(top_stocks)} 只股票:")
    for i, stock in enumerate(top_stocks, 1):
        print(f"{i}. {stock['code']} {stock['name']} - 资金得分: {stock['fund_flow_score']}")
    
    # 保存到文件
    if top_stocks:
        saved_file = fetcher.save_to_file(top_stocks)
        print(f"\n数据已保存到: {saved_file}")