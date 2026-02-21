# Flask-App 访问指南

## 🚀 应用状态

**应用名称**: Flask Stock Data App  
**启动时间**: 2026-02-20 12:18  
**运行状态**: ✅ 正常运行  
**进程ID**: 2779462  
**监听端口**: 5000  

## 🌐 访问地址

### 1. Tailscale 地址（推荐）
```
主地址: http://100.121.110.111:5000
IPv6地址: http://[fd7a:115c:a1e0::c13b:6e6f]:5000
```

### 2. 本地地址
```
本地回环: http://127.0.0.1:5000
服务器内网: http://10.0.0.16:5000
所有接口: http://0.0.0.0:5000
```

### 3. 公网地址（如果配置了端口转发）
```
服务器IP: http://119.29.145.27:5000
（需要配置防火墙和端口转发）
```

## 📱 快速访问链接

### 核心页面
- **首页**: http://100.121.110.111:5000
- **健康检查**: http://100.121.110.111:5000/api/health
- **系统信息**: http://100.121.110.111:5000/api/info

### 股票数据API
- **资金流入前10股票**: http://100.121.110.111:5000/api/stock/top_fund_flow?days=5&top_n=10
- **股票详情示例**: http://100.121.110.111:5000/api/stock/details/000001
- **API文档**: http://100.121.110.111:5000/api/stock/docs
- **实时数据**: http://100.121.110.111:5000/api/stock/realtime?codes=000001,000002
- **历史数据**: http://100.121.110.111:5000/api/stock/historical?code=000001

## 🔧 功能验证

### 1. 健康检查
```bash
curl http://100.121.110.111:5000/api/health
```

### 2. 获取股票数据
```bash
# 获取最近5天资金流入前10的股票
curl "http://100.121.110.111:5000/api/stock/top_fund_flow?days=5&top_n=10"

# 获取CSV格式
curl "http://100.121.110.111:5000/api/stock/top_fund_flow?days=5&top_n=10&format=csv" -o stocks.csv
```

### 3. 网页访问
直接在浏览器中打开: http://100.121.110.111:5000

## 🛠️ 应用管理

### 启动应用
```bash
cd /home/ubuntu/flask-app
source venv/bin/activate
python app.py
```

### 停止应用
```bash
# 查找进程ID
ps aux | grep "python app.py" | grep -v grep

# 停止进程
kill <进程ID>
```

### 查看日志
```bash
# 实时查看应用日志
tail -f /home/ubuntu/flask-app/logs/flask.log

# 查看股票模块日志
tail -f /home/ubuntu/flask-app/stock_data/logs/stock_data.log
```

## 📊 系统信息

### 服务器信息
- **服务器IP**: 119.29.145.27
- **Tailscale IP**: 100.121.110.111
- **操作系统**: Ubuntu 24.04
- **Python版本**: 3.12.3
- **Flask版本**: 3.1.2

### 应用模块
- ✅ **Flask Web框架** - 正常运行
- ✅ **股票数据模块** - 已集成，功能完整
- ✅ **Reddit推送模块** - 已存在，定时运行
- ✅ **测试框架** - 已配置，可运行测试

### 数据目录
- **应用日志**: `/home/ubuntu/flask-app/logs/`
- **股票数据**: `/home/ubuntu/flask-app/stock_data/`
- **Reddit数据**: `/home/ubuntu/flask-app/reddit_output/`
- **测试报告**: `/home/ubuntu/flask-app/coverage_report/`

## 🔒 安全说明

### 当前配置
- **调试模式**: 开启（开发环境）
- **密钥管理**: 使用环境变量
- **访问控制**: 无认证（开发环境）
- **日志记录**: 完整记录

### 生产建议
1. **关闭调试模式**: 设置 `FLASK_DEBUG=False`
2. **设置安全密钥**: 设置 `SECRET_KEY` 环境变量
3. **添加认证**: 实现API密钥或OAuth认证
4. **启用HTTPS**: 配置SSL证书
5. **配置防火墙**: 限制访问IP

## 📈 监控检查

### 服务状态
```bash
# 检查进程状态
ps aux | grep "python app.py" | grep -v grep

# 检查端口监听
netstat -tlnp | grep :5000

# 检查服务响应
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/api/health
```

### 资源使用
```bash
# 查看内存使用
ps -o pid,user,%mem,command ax | grep app.py

# 查看磁盘空间
df -h /home/ubuntu/flask-app/

# 查看日志大小
du -sh /home/ubuntu/flask-app/logs/
```

## 🚨 故障排除

### 常见问题

#### 1. 无法访问
```bash
# 检查Tailscale状态
tailscale status

# 检查防火墙
sudo ufw status

# 测试本地访问
curl http://127.0.0.1:5000/api/health
```

#### 2. 应用未启动
```bash
# 重新启动
cd /home/ubuntu/flask-app
source venv/bin/activate
python app.py &

# 检查错误日志
cat /home/ubuntu/flask-app/logs/flask.log | tail -50
```

#### 3. 模块导入错误
```bash
# 检查Python路径
python -c "import sys; print(sys.path)"

# 检查依赖安装
pip list | grep -E "(Flask|pandas|numpy)"
```

### 联系支持
- **应用日志**: `/home/ubuntu/flask-app/logs/flask.log`
- **股票日志**: `/home/ubuntu/flask-app/stock_data/logs/stock_data.log`
- **错误报告**: 查看上述日志文件获取详细信息

## 🎯 使用示例

### 网页访问
1. 确保已连接 Tailscale 网络
2. 在浏览器中打开: http://100.121.110.111:5000
3. 查看首页功能说明
4. 点击链接测试各个API端点

### 命令行访问
```bash
# 测试健康状态
curl http://100.121.110.111:5000/api/health | jq .

# 获取股票数据
curl "http://100.121.110.111:5000/api/stock/top_fund_flow?days=5&top_n=3" | jq '.data[] | {code:.code, name:.name, score:.fund_flow_score}'

# 下载CSV数据
curl "http://100.121.110.111:5000/api/stock/top_fund_flow?days=5&top_n=10&format=csv" > stocks.csv
```

### 自动化脚本
```python
import requests

# 获取股票数据
response = requests.get("http://100.121.110.111:5000/api/stock/top_fund_flow", 
                       params={"days": 5, "top_n": 10})
stocks = response.json()["data"]

for stock in stocks:
    print(f"{stock['code']} {stock['name']}: {stock['fund_flow_score']}")
```

---
**最后更新**: 2026-02-20 12:18  
**应用版本**: 2.0.0  
**维护者**: Friday (OpenClaw 助手)  
**状态**: ✅ 生产环境运行中