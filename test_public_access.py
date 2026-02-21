#!/usr/bin/env python3
"""
测试公网访问脚本
"""

import socket
import requests
import sys
from datetime import datetime

def get_public_ip():
    """获取公网IP"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        try:
            response = requests.get('http://ifconfig.me', timeout=5)
            return response.text.strip()
        except:
            return "无法获取公网IP"

def check_port_open(ip, port, timeout=2):
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_local_access():
    """测试本地访问"""
    try:
        response = requests.get('http://127.0.0.1:5000/api/health', timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)

def test_internal_access():
    """测试内网访问"""
    try:
        response = requests.get('http://10.0.0.16:5000/api/health', timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)

def main():
    """主测试函数"""
    print("=" * 60)
    print("🌐 Flask-App 公网访问测试")
    print("=" * 60)
    
    # 获取公网IP
    public_ip = get_public_ip()
    print(f"📡 公网IP地址: {public_ip}")
    print(f"📡 服务器内网IP: 10.0.0.16")
    print(f"📡 Tailscale IP: 100.121.110.111")
    print(f"🌐 访问地址: http://{public_ip}:5000")
    
    # 检查端口
    print("\n🔍 检查端口状态...")
    port_open = check_port_open(public_ip, 5000)
    print(f"   端口5000对外状态: {'✅ 开放' if port_open else '❌ 关闭'}")
    
    # 测试本地访问
    print("\n🏠 测试本地访问...")
    local_ok, local_data = test_local_access()
    print(f"   本地访问 (127.0.0.1:5000): {'✅ 成功' if local_ok else '❌ 失败'}")
    if local_ok and local_data:
        print(f"   服务状态: {local_data.get('status', '未知')}")
        print(f"   服务版本: {local_data.get('version', '未知')}")
    
    # 测试内网访问
    print("\n🔗 测试内网访问...")
    internal_ok, internal_data = test_internal_access()
    print(f"   内网访问 (10.0.0.16:5000): {'✅ 成功' if internal_ok else '❌ 失败'}")
    
    # 生成访问指南
    print("\n" + "=" * 60)
    print("🚀 公网访问指南")
    print("=" * 60)
    
    print(f"\n🌐 主要访问地址:")
    print(f"   公网地址: http://{public_ip}:5000")
    print(f"   Tailscale: http://100.121.110.111:5000")
    print(f"   内网地址: http://10.0.0.16:5000")
    print(f"   本地地址: http://127.0.0.1:5000")
    
    print(f"\n🔗 核心API端点:")
    print(f"   首页: http://{public_ip}:5000")
    print(f"   健康检查: http://{public_ip}:5000/api/health")
    print(f"   股票数据: http://{public_ip}:5000/api/stock/top_fund_flow?days=5&top_n=10")
    print(f"   API文档: http://{public_ip}:5000/api/stock/docs")
    
    print(f"\n📱 快速测试命令:")
    print(f"   # 健康检查")
    print(f"   curl http://{public_ip}:5000/api/health")
    print(f"   ")
    print(f"   # 获取股票数据")
    print(f'   curl "http://{public_ip}:5000/api/stock/top_fund_flow?days=5&top_n=3"')
    
    print(f"\n⚠️  注意事项:")
    if not port_open:
        print(f"   1. 端口5000可能被云服务商防火墙阻挡")
        print(f"   2. 需要配置安全组/防火墙规则")
        print(f"   3. 检查服务器提供商的控制面板")
    else:
        print(f"   1. 端口已开放，可以尝试从外部访问")
        print(f"   2. 确保网络连接正常")
        print(f"   3. 如有问题检查服务器防火墙设置")
    
    print(f"\n🔧 防火墙配置建议:")
    print(f"   # 如果使用UFW")
    print(f"   sudo ufw allow 5000/tcp")
    print(f"   sudo ufw reload")
    print(f"   ")
    print(f"   # 如果使用iptables")
    print(f"   sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT")
    
    print(f"\n📊 测试总结:")
    print(f"   公网IP: {public_ip}")
    print(f"   端口状态: {'开放' if port_open else '需要配置'}")
    print(f"   本地服务: {'正常运行' if local_ok else '异常'}")
    print(f"   内网访问: {'正常' if internal_ok else '异常'}")
    
    if port_open and local_ok:
        print(f"\n🎉 恭喜！Flask-App 应该可以通过公网访问")
        print(f"   请尝试访问: http://{public_ip}:5000")
    else:
        print(f"\n⚠️  需要配置网络设置才能从公网访问")
        print(f"   请检查防火墙和安全组规则")

if __name__ == '__main__':
    main()