#!/usr/bin/env python3
"""
测试股票数据模块
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stock_config():
    """测试配置模块"""
    print("🔧 测试配置模块...")
    try:
        from stock_config import get_config, validate_config, get_date_range
        
        config = get_config()
        print(f"✅ 配置加载成功")
        print(f"   数据源: {list(config['data_sources'].keys())}")
        print(f"   获取天数: {config['data_fetch']['days_back']}")
        print(f"   前N名: {config['data_fetch']['top_n']}")
        
        validate_config()
        print("✅ 配置验证通过")
        
        date_range = get_date_range(5)
        print(f"✅ 日期范围: {date_range['start_date']} 到 {date_range['end_date']}")
        
        return True
    except Exception as e:
        print(f"❌ 配置模块测试失败: {e}")
        return False

def test_stock_fetcher():
    """测试数据获取器"""
    print("\n📊 测试股票数据获取器...")
    try:
        from stock_data_fetcher import StockDataFetcher
        
        fetcher = StockDataFetcher(data_source='eastmoney', use_cache=True)
        print("✅ 股票数据获取器初始化成功")
        
        # 获取最近5天资金流入前10的股票
        stocks = fetcher.get_top_fund_flow_stocks(days=5, top_n=10)
        
        if stocks:
            print(f"✅ 成功获取 {len(stocks)} 只股票数据")
            print("\n📈 资金流入前10股票:")
            for i, stock in enumerate(stocks[:5], 1):  # 只显示前5个
                print(f"  {i}. {stock['code']} {stock['name']}")
                print(f"     价格: {stock['current_price']} 涨跌: {stock['change_percent']}%")
                print(f"     资金得分: {stock['fund_flow_score']} 建议: {stock['recommendation']}")
            
            # 保存到文件
            saved_file = fetcher.save_to_file(stocks)
            if saved_file:
                print(f"✅ 数据已保存到: {saved_file}")
            
            # 测试获取股票详情
            if stocks:
                details = fetcher.get_stock_details(stocks[0]['code'])
                if details:
                    print(f"✅ 股票详情获取成功: {details['code']} - {details['name']}")
            
            return True
        else:
            print("❌ 未获取到股票数据")
            return False
            
    except Exception as e:
        print(f"❌ 数据获取器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stock_api():
    """测试API模块"""
    print("\n🌐 测试股票API模块...")
    try:
        from stock_api import get_stock_fetcher
        
        fetcher = get_stock_fetcher()
        print("✅ API模块初始化成功")
        
        # 测试API端点功能
        from flask import Flask
        from stock_api import stock_bp
        
        app = Flask(__name__)
        app.register_blueprint(stock_bp)
        
        print("✅ Flask蓝图注册成功")
        print("   可用端点:")
        print("     GET /api/stock/health")
        print("     GET /api/stock/top_fund_flow")
        print("     GET /api/stock/details/<code>")
        print("     GET /api/stock/historical")
        print("     GET /api/stock/realtime")
        print("     GET /api/stock/config")
        
        return True
    except Exception as e:
        print(f"❌ API模块测试失败: {e}")
        return False

def test_integration():
    """测试集成"""
    print("\n🔗 测试集成到Flask应用...")
    try:
        from app import create_app
        
        app = create_app()
        print("✅ Flask应用创建成功")
        
        # 检查路由
        with app.test_client() as client:
            # 测试首页
            response = client.get('/')
            if response.status_code == 200:
                print("✅ 首页访问成功")
            
            # 测试健康检查
            response = client.get('/api/health')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('status') == 'healthy':
                    print("✅ 健康检查通过")
            
            # 测试股票API（如果可用）
            response = client.get('/api/stock/health')
            if response.status_code == 200:
                print("✅ 股票API健康检查通过")
        
        return True
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def install_dependencies():
    """安装依赖"""
    print("\n📦 检查依赖安装...")
    try:
        import pandas
        import numpy
        import bs4
        import lxml
        
        print("✅ 核心依赖已安装")
        return True
    except ImportError as e:
        print(f"⚠️  缺少依赖: {e}")
        print("   请运行: pip install -r requirements.txt")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 Flask-App 股票数据模块测试")
    print("=" * 60)
    
    results = []
    
    # 检查依赖
    if not install_dependencies():
        print("\n⚠️  请先安装依赖再运行测试")
        return
    
    # 运行测试
    results.append(('配置模块', test_stock_config()))
    results.append(('数据获取器', test_stock_fetcher()))
    results.append(('API模块', test_stock_api()))
    results.append(('集成测试', test_integration()))
    
    # 显示结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    print("-" * 60)
    print(f"总计: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！股票数据模块已成功集成。")
        print("\n🚀 下一步:")
        print("  1. 运行Flask应用: python app.py")
        print("  2. 访问 http://localhost:5000")
        print("  3. 测试股票API端点")
    else:
        print("\n⚠️  部分测试失败，请检查问题。")

if __name__ == '__main__':
    main()