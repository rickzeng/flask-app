#!/usr/bin/env python3
"""
腾讯财经数据格式分析
"""

import requests

# 获取单只股票
url = "https://qt.gtimg.cn/q=sh600519"
response = requests.get(url)
data = response.content.decode('gbk')

print("原始数据:")
print(data)
print()

# 提取数据
import re
match = re.search(r'v_([a-z]+)(\d+)="(.+?)"', data)
if match:
    code_prefix = match.group(1)  # sh 或 sz
    code_num = match.group(2)  # 600519
    stock_data = match.group(3)  # 数据部分

    # 按 ~ 分割
    fields = stock_data.split('~')

    print(f"股票代码: {code_prefix}{code_num}")
    print(f"字段数量: {len(fields)}")
    print()

    print("所有字段:")
    for i, field in enumerate(fields):
        print(f"{i:2d}: {field}")
