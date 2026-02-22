#!/usr/bin/env python3
"""
腾讯财经数据获取器（最终修复版）
"""

import requests
import re
from typing import Dict, List, Optional

class TencentStockFetcher:
    """腾讯财经数据获取器"""

    def __init__(self):
        """初始化"""
        self.base_url = "https://qt.gtimg.cn/q="

    def parse_stock_data(self, data: str) -> Optional[Dict]:
        """
        解析腾讯财经股票数据

        数据格式分析（基于实际数据）:
        v_sh600519="1~贵州茅台~600519~1485.30~1486.60~1486.60~41679~20986~20693~1485.30~2~1485.28~8~1485.18~1~1485.15~1~1485.10~21~1485.39~17~1485.49~1~1485.50~25~1485.55~1~1485.57~1~~20260213161424~-1.30~-0.09~1507.80~1470.58~1485.30/41679/6216379203~41679~621638~0.33~20.66~~1507.80~1470.58~2.50~18599.97~18599.97~8.19~1635.26~1337.94~0.84~-12~1491.49~21.59~21.57~~~0.63~621637.9203~0.0000~0~ ~GP-A~7.85~-1.96~3.48~35.02~30.58~1606.43~1322.01~6.02~7.47~2.64~1252270215~1252270215~-15.38~-0.91~1252270215~~~5.08~0.03~~CNY~0~___D__F__N~1485.00~134~"

        字段分析:
        0: 状态
        1: 名称
        2: 代码
        3: 当前价
        4: 昨收
        5: 今开
        6-8: (未知字段)
        9: 未知价格
        10-29: (未知字段)
        30: 日期时间戳
        31: 涨跌额
        32: 涨跌幅
        """
        try:
            # 使用正则表达式提取股票数据
            pattern = r'v_([a-z]+)(\d+)="(.+?)"'
            match = re.search(pattern, data)

            if not match:
                return None

            code_prefix = match.group(1)  # sh 或 sz
            code_num = match.group(2)  # 600519
            stock_data = match.group(3)  # 数据部分

            # 按 ~ 分割
            fields = stock_data.split('~')

            if len(fields) < 33:
                return None

            # 解析数据
            stock_info = {
                'code': f"{code_prefix}{code_num}",
                'name': fields[1],
                'current_price': float(fields[3]) if fields[3] else 0,
                'preclose': float(fields[4]) if fields[4] else 0,
                'open_price': float(fields[5]) if fields[5] else 0,
                'change': float(fields[31]) if len(fields) > 31 and fields[31] else 0,
                'change_percent': float(fields[32]) if len(fields) > 32 and fields[32] else 0,
                'datetime': fields[30],
                'status': fields[0],
            }

            # 计算涨跌额和涨跌幅（如果计算不正确）
            if stock_info['preclose'] > 0:
                if stock_info['change'] == 0:
                    stock_info['change'] = stock_info['current_price'] - stock_info['preclose']
                if stock_info['change_percent'] == 0:
                    stock_info['change_percent'] = (stock_info['current_price'] - stock_info['preclose']) / stock_info['preclose'] * 100

            return stock_info

        except Exception as e:
            print(f"解析数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_stock_data(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票数据

        Args:
            stock_code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票信息字典
        """
        try:
            url = self.base_url + stock_code
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # 读取为 GBK 编码
                data = response.content.decode('gbk')
                return self.parse_stock_data(data)
            else:
                print(f"请求失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return None

    def get_multiple_stocks(self, stock_codes: List[str]) -> List[Dict]:
        """
        获取多只股票数据

        Args:
            stock_codes: 股票代码列表（如 ['sh600519', 'sz000001']）

        Returns:
            股票信息列表
        """
        try:
            url = self.base_url + ','.join(stock_codes)
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # 读取为 GBK 编码
                data = response.content.decode('gbk')

                # 按分号分割
                stocks = data.split(';')

                result = []
                for stock in stocks:
                    stock_info = self.parse_stock_data(stock)
                    if stock_info:
                        result.append(stock_info)

                return result
            else:
                print(f"请求失败: {response.status_code}")
                return []

        except Exception as e:
            print(f"获取多只股票数据失败: {e}")
            return []

    def format_stock_code(self, code: str) -> str:
        """
        格式化股票代码

        Args:
            code: 原始代码（如 600519, 000001, 300750）

        Returns:
            格式化后的代码（如 sh600519, sz000001, sz300750）
        """
        if not code:
            return code

        code = code.strip()

        # 沪市代码
        if code.startswith('6') or code.startswith('5'):
            return 'sh' + code.zfill(6)
        # 深市主板
        elif code.startswith('0'):
            return 'sz' + code.zfill(6)
        # 创业板
        elif code.startswith('3'):
            return 'sz' + code.zfill(6)
        # 科创板
        elif code.startswith('688'):
            return 'sh' + code.zfill(6)
        else:
            return code

if __name__ == '__main__':
    # 测试腾讯财经数据获取器
    fetcher = TencentStockFetcher()

    # 测试1: 获取单只股票
    print("=" * 60)
    print("测试1: 获取单只股票（贵州茅台 600519）")
    print("=" * 60)

    stock_data = fetcher.get_stock_data('sh600519')
    if stock_data:
        print(f"股票代码: {stock_data['code']}")
        print(f"股票名称: {stock_data['name']}")
        print(f"当前价格: {stock_data['current_price']}")
        print(f"昨收价格: {stock_data['preclose']}")
        print(f"今开价格: {stock_data['open_price']}")
        print(f"涨跌额: {stock_data['change']}")
        print(f"涨跌幅: {stock_data['change_percent']:.2f}%")
        print(f"日期时间: {stock_data['datetime']}")
        print(f"状态: {stock_data['status']}")

    # 测试2: 获取多只股票
    print("\n" + "=" * 60)
    print("测试2: 获取多只股票")
    print("=" * 60)

    stocks = fetcher.get_multiple_stocks(['sh600519', 'sz000001', 'sz300750'])
    print(f"获取到 {len(stocks)} 只股票数据:")
    for stock in stocks:
        print(f"  {stock['name']}({stock['code']}): {stock['current_price']}, 涨跌幅: {stock['change_percent']:.2f}%")

    # 测试3: 格式化代码
    print("\n" + "=" * 60)
    print("测试3: 格式化股票代码")
    print("=" * 60)

    codes = ['600519', '000001', '300750', '688981']
    for code in codes:
        formatted = fetcher.format_stock_code(code)
        print(f"  {code} -> {formatted}")
