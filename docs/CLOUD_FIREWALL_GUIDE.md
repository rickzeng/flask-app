# 云服务商防火墙配置指南

## 📋 当前状态

### 服务器信息
- **公网IP**: 119.29.145.27
- **服务端口**: 5000
- **应用状态**: ✅ 正常运行（本地可访问）
- **服务器防火墙**: ✅ UFW已配置（端口5000已开放）

### 问题诊断
- ✅ 本地访问: 正常 (http://127.0.0.1:5000)
- ✅ 内网访问: 正常 (http://10.0.0.16:5000)  
- ❌ 公网访问: 被阻挡 (http://119.29.145.27:5000)
- **原因**: 云服务商安全组未开放端口5000

## 🌐 云服务商配置

### 腾讯云配置步骤

#### 1. 登录腾讯云控制台
- 访问: https://console.cloud.tencent.com/cvm
- 选择地区: 广州/上海/北京等（根据服务器所在地）

#### 2. 配置安全组
1. 进入「安全组」页面
2. 找到关联到服务器 `119.29.145.27` 的安全组
3. 点击「编辑规则」

#### 3. 添加入站规则
```
规则类型: 自定义
来源: 0.0.0.0/0 或 指定IP段
协议端口: TCP:5000
策略: 允许
备注: Flask-App Web服务
```

#### 4. 保存并应用
1. 点击「完成」
2. 确保规则已应用到当前服务器
3. 等待1-2分钟生效

### 阿里云配置步骤

#### 1. 登录阿里云控制台
- 访问: https://ecs.console.aliyun.com
- 选择地域

#### 2. 配置安全组
1. 进入「安全组」页面
2. 找到关联实例的安全组
3. 点击「配置规则」

#### 3. 添加入方向规则
```
授权策略: 允许
协议类型: 自定义TCP
端口范围: 5000/5000
授权对象: 0.0.0.0/0
优先级: 1
描述: Flask-App服务端口
```

### AWS配置步骤

#### 1. 登录AWS控制台
- 访问: https://console.aws.amazon.com/ec2
- 选择区域

#### 2. 配置安全组
1. 进入「Security Groups」
2. 找到关联实例的安全组
3. 点击「Edit inbound rules」

#### 3. 添加入站规则
```
Type: Custom TCP
Port range: 5000
Source: 0.0.0.0/0
Description: Flask-App Web Service
```

## 🔧 备用解决方案

### 方案1: 使用反向代理（推荐）
```nginx
# Nginx配置示例
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
优点: 可以使用标准HTTP端口(80/443)，无需特殊配置

### 方案2: 使用SSH隧道
```bash
# 从本地建立隧道
ssh -L 5000:localhost:5000 user@119.29.145.27

# 然后本地访问
curl http://localhost:5000/api/health
```

### 方案3: 使用Cloudflare Tunnel
```bash
# 安装Cloudflare Tunnel
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# 创建隧道
cloudflared tunnel create flask-app
cloudflared tunnel route dns flask-app your-app.example.com
cloudflared tunnel run flask-app
```

## 📱 临时访问方案

### 1. 使用Tailscale（已配置）
```
访问地址: http://100.121.110.111:5000
优点: 无需公网端口，安全可靠
```

### 2. 修改监听端口
```python
# 修改app.py，使用标准HTTP端口
app.run(host='0.0.0.0', port=80, debug=False)
```
注意: 需要sudo权限运行

### 3. 端口转发测试
```bash
# 临时端口转发（需要root）
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000
```

## 🧪 验证配置

### 配置后测试命令
```bash
# 测试端口开放
nc -zv 119.29.145.27 5000

# 测试HTTP访问
curl -v http://119.29.145.27:5000/api/health

# 使用telnet测试
telnet 119.29.145.27 5000
```

### 预期结果
```
# 成功响应
HTTP/1.0 200 OK
Content-Type: application/json
{"status": "healthy", "service": "flask-app", ...}
```

## ⚠️ 安全建议

### 生产环境配置
1. **限制访问IP**: 不要使用 `0.0.0.0/0`，指定可信IP段
2. **启用HTTPS**: 配置SSL证书，使用端口443
3. **添加认证**: 实现API密钥或用户认证
4. **启用WAF**: 配置Web应用防火墙
5. **定期更新**: 保持系统和依赖更新

### 最小权限原则
```
# 推荐的安全组规则
来源: 办公室IP/家庭IP/VPN IP
协议: TCP:5000
策略: 允许
```

## 🔍 故障排除

### 常见问题

#### 1. 配置后仍无法访问
```bash
# 检查服务器监听
netstat -tlnp | grep :5000

# 检查防火墙
sudo ufw status

# 检查云服务商控制台
# 确认规则已保存并应用
```

#### 2. 端口被其他服务占用
```bash
# 查找占用端口的进程
sudo lsof -i :5000

# 停止冲突进程或修改端口
```

#### 3. 应用未启动
```bash
# 检查应用进程
ps aux | grep "python app.py"

# 查看应用日志
tail -f /home/ubuntu/flask-app/logs/flask.log
```

#### 4. DNS解析问题
```bash
# 直接使用IP测试
curl http://119.29.145.27:5000/api/health

# 检查DNS解析
nslookup your-domain.com
```

## 📞 支持信息

### 服务器详情
- **公网IP**: 119.29.145.27
- **内网IP**: 10.0.0.16
- **Tailscale IP**: 100.121.110.111
- **操作系统**: Ubuntu 24.04 LTS
- **应用目录**: /home/ubuntu/flask-app/

### 应用信息
- **服务端口**: 5000
- **应用状态**: 运行中
- **进程ID**: [当前运行进程ID]
- **启动命令**: `python app.py`
- **日志文件**: `/home/ubuntu/flask-app/logs/flask.log`

### 联系支持
1. 登录云服务商控制台配置安全组
2. 配置后等待1-5分钟生效
3. 使用测试命令验证访问
4. 如有问题检查应用日志

---
**最后更新**: 2026-02-20 12:22  
**配置状态**: 等待云服务商安全组配置  
**临时访问**: 使用Tailscale地址 http://100.121.110.111:5000