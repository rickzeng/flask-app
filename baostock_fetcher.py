#!/usr/bin/env python3
"""
Baostock 数据获取器
"""

import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class BaostockFetcher:
    """Baostock 数据获取器"""

    def __init__(self):
        """初始化"""
        self.login_status = None
        self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('baostock_fetcher')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def login(self) -> bool:
        """登录系统"""
        lg = bs.login()
        self.login_status = lg
        if lg.error_code == '0':
            self.logger.info("Baostock 登录成功")
            return True
        else:
            self.logger.error(f"Baostock 登录失败: {lg.error_msg}")
            return False

    def logout(self):
        """登出系统"""
        bs.logout()
        self.logger.info("Baostock 已登出")

    def get_stock_basic(self, stock_code: str) -> Optional[Dict]:
        """获取股票基本信息

        Args:
            stock_code: 股票代码（如 sh.600519）

        Returns:
            股票基本信息字典
        """
        if not self.login():
            self.login()

        rs = bs.query_stock_basic(code=stock_code)
        if rs.error_code == '0':
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            if len(data_list) > 0:
                data = data_list[0]
                return {
                    'code': data[0],
                    'name': data[1],
                    'industry': data[3],
                    'listing_date': data[4],
                }
        return None

    def get_history_data(self, stock_code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取历史K线数据

        Args:
            stock_code: 股票代码（如 sh.600519）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            历史K线数据列表
        """
        if not self.login():
            self.login()

        rs = bs.query_history_k_data_plus(
            stock_code,
            fields="date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"
        )

        if rs.error_code == '0':
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            self.logger.info(f"获取到 {len(data_list)} 条历史数据")
            return data_list
        else:
            self.logger.error(f"获取历史数据失败: {rs.error_msg}")
            return []

    def get_latest_data(self, stock_code: str) -> Optional[Dict]:
        """获取最新数据

        Args:
            stock_code: 股票代码（如 sh.600519）

        Returns:
            最新数据字典
        """
        # 获取最近30天的数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        history_data = self.get_history_data(stock_code, start_date, end_date)
        if len(history_data) > 0:
            latest = history_data[-1]
            return {
                'date': latest[0],
                'code': latest[1],
                'open': float(latest[2]),
                'high': float(latest[3]),
                'low': float(latest[4]),
                'close': float(latest[5]),
                'preclose': float(latest[6]),
                'volume': float(latest[7]),
                'amount': float(latest[8]),
                'turn': float(latest[10]),
                'pctChg': float(latest[12]),
                'peTTM': float(latest[13]),
                'pbMRQ': float(latest[14]),
            }
        return None

    def get_profit_data(self, stock_code: str, year: int, quarter: int) -> Optional[Dict]:
        """获取利润数据

        Args:
            stock_code: 股票代码（如 sh.600519）
            year: 年份
            quarter: 季度

        Returns:
            利润数据字典
        """
        if not self.login():
            self.login()

        rs = bs.query_profit_data(code=stock_code, year=year, quarter=quarter)
        if rs.error_code == '0':
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            if len(data_list) > 0:
                data = data_list[0]
                return {
                    'roeAvg': data[3],
                    'npMargin': data[4],
                    'gpMargin': data[5],
                    'netProfit': data[9],
                }
        return None

    def get_all_stocks(self, date: str) -> List[Dict]:
        """获取所有股票列表

        Args:
            date: 日期（YYYY-MM-DD）

        Returns:
            股票列表
        """
        if not self.login():
            self.login()

        rs = bs.query_all_stock(day=date)
        if rs.error_code == '0':
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            self.logger.info(f"获取到 {len(data_list)} 只股票")
            return data_list
        else:
            self.logger.error(f"获取股票列表失败: {rs.error_msg}")
            return []

if __name__ == '__main__':
    # 测试 BaostockFetcher
    fetcher = BaostockFetcher()

    # 登录
    if fetcher.login():
        # 获取股票基本信息
        print("\n股票基本信息:")
        basic_info = fetcher.get_stock_basic('sh.600519')
        if basic_info:
            print(f"代码: {basic_info['code']}")
            print(f"名称: {basic_info['name']}")
            print(f"行业: {basic_info['industry']}")

        # 获取最新数据
        print("\n最新数据:")
        latest_data = fetcher.get_latest_data('sh.600519')
        if latest_data:
            print(f"日期: {latest_data['date']}")
            print(f"收盘价: {latest_data['close']}")
            print(f"涨跌幅: {latest_data['pctChg']}%")
            print(f"市盈率: {latest_data['peTTM']}")

        # 登出
        fetcher.logout()
