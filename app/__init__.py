"""
Flask应用初始化文件
"""

import sys
import os


def create_app(config_name=None):
    """应用工厂函数"""
    # 添加项目根目录到路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from app import create_app as _create_app

    return _create_app(config_name)


__all__ = ["create_app"]
