#!/usr/bin/env python3
"""
示例：使用 CDP (Chrome DevTools Protocol) 控制 Microsoft Edge
"""

import json
import requests
import websocket
import time

def list_cdp_targets():
    """列出所有可用的 CDP 目标"""
    try:
        response = requests.get('http://localhost:9222/json/list', timeout=5)
        return response.json()
    except Exception as e:
        print(f"无法连接到 Edge CDP: {e}")
        return []

def navigate_to_url(ws_url, url):
    """导航到指定 URL"""
    try:
        ws = websocket.create_connection(ws_url)
        
        # 启用必要的域
        enable_cmds = [
            {
                "id": 1,
                "method": "Page.enable",
                "params": {}
            },
            {
                "id": 2,
                "method": "Runtime.enable",
                "params": {}
            }
        ]
        
        for cmd in enable_cmds:
            ws.send(json.dumps(cmd))
            response = ws.recv()
            print(f"启用响应: {response}")
        
        # 导航到 URL
        navigate_cmd = {
            "id": 3,
            "method": "Page.navigate",
            "params": {"url": url}
        }
        
        ws.send(json.dumps(navigate_cmd))
        response = ws.recv()
        print(f"导航响应: {response}")
        
        # 等待页面加载
        time.sleep(2)
        
        # 获取页面标题
        title_cmd = {
            "id": 4,
            "method": "Runtime.evaluate",
            "params": {
                "expression": "document.title"
            }
        }
        
        ws.send(json.dumps(title_cmd))
        response = ws.recv()
        result = json.loads(response)
        
        if 'result' in result and 'result' in result['result']:
            title = result['result']['result']['value']
            print(f"页面标题: {title}")
        
        ws.close()
        return True
        
    except Exception as e:
        print(f"导航失败: {e}")
        return False

def main():
    print("=== Edge CDP 示例 ===")
    
    # 列出所有目标
    targets = list_cdp_targets()
    
    if not targets:
        print("没有找到可用的 CDP 目标")
        print("请确保 Edge 正在运行: microsoft-edge --headless --remote-debugging-port=9222")
        return
    
    print(f"找到 {len(targets)} 个目标:")
    for i, target in enumerate(targets):
        print(f"{i+1}. {target['title']} ({target['url']})")
        print(f"   WebSocket: {target['webSocketDebuggerUrl']}")
    
    # 使用第一个目标
    if targets:
        target = targets[0]
        ws_url = target['webSocketDebuggerUrl']
        
        print(f"\n使用目标: {target['title']}")
        
        # 测试导航到 Flask 应用
        print("\n1. 导航到本地 Flask 应用...")
        navigate_to_url(ws_url, "http://localhost:5000")
        
        # 测试导航到 Google
        print("\n2. 导航到 Google...")
        navigate_to_url(ws_url, "https://www.google.com")
        
        print("\n=== 示例完成 ===")

if __name__ == '__main__':
    main()