#!/usr/bin/env python3
"""
测试运行脚本
"""

import unittest
import sys
import os

def run_all_tests():
    """运行所有测试"""
    # 添加项目根目录到 Python 路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 发现并运行测试
    loader = unittest.TestLoader()
    
    # 指定测试目录
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


def run_specific_test(test_name):
    """运行特定测试"""
    # 添加项目根目录到 Python 路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 导入测试模块
    test_module_name = f'tests.test_{test_name}'
    
    try:
        module = __import__(test_module_name, fromlist=['*'])
    except ImportError:
        print(f"错误: 找不到测试模块 '{test_module_name}'")
        print("可用的测试模块:")
        for file in os.listdir('tests'):
            if file.startswith('test_') and file.endswith('.py'):
                print(f"  - {file[5:-3]}")
        return False
    
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromModule(module)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    try:
        import coverage
    except ImportError:
        print("错误: 未安装 coverage 模块")
        print("请运行: pip install coverage")
        return False
    
    # 初始化覆盖率
    cov = coverage.Coverage(
        source=['.'],
        omit=['tests/*', 'venv/*', '__pycache__/*']
    )
    cov.start()
    
    # 运行测试
    success = run_all_tests()
    
    # 停止覆盖率收集
    cov.stop()
    cov.save()
    
    # 生成报告
    print("\n" + "="*60)
    print("覆盖率报告")
    print("="*60)
    
    # 控制台报告
    cov.report()
    
    # HTML 报告
    cov.html_report(directory='coverage_report')
    print(f"\nHTML 报告已生成: file://{os.path.abspath('coverage_report/index.html')}")
    
    return success


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='运行 Flask-App 测试')
    parser.add_argument('--test', '-t', help='运行特定测试（不包含"test_"前缀）')
    parser.add_argument('--coverage', '-c', action='store_true', help='运行测试并生成覆盖率报告')
    parser.add_argument('--all', '-a', action='store_true', help='运行所有测试（默认）')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_specific_test(args.test)
    elif args.coverage:
        success = run_with_coverage()
    else:
        success = run_all_tests()
    
    # 根据测试结果退出
    sys.exit(0 if success else 1)