# Flask 应用程序

这是一个使用 Python Flask 框架创建的简单 Web 应用程序。

## 功能特性

- 主页展示欢迎信息
- RESTful API 端点
- 健康检查接口
- 调试模式支持

## API 端点

### `GET /`
主页，显示欢迎信息和 API 链接

### `GET /api/hello`
打招呼接口，返回 JSON 响应

### `GET /api/health`
健康检查接口，返回服务状态

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行应用程序
```bash
# 方式1：直接运行 app.py
python app.py

# 方式2：使用启动脚本
python run.py

# 方式3：使用 Flask CLI
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```

### 3. 访问应用程序
- 主页：http://localhost:5000
- API 端点：http://localhost:5000/api/hello
- 健康检查：http://localhost:5000/api/health

## 项目结构
```
flask-app/
├── app.py          # 主应用程序文件
├── requirements.txt # 依赖文件
├── run.py          # 启动脚本
├── README.md       # 项目说明
└── config.py       # 配置文件（可选）
```

## 配置

可以通过环境变量配置应用程序：

```bash
export FLASK_DEBUG=True  # 启用调试模式
export FLASK_ENV=development  # 设置环境
```

## 开发

### 代码风格
- 遵循 PEP 8 代码规范
- 使用类型提示（Type Hints）
- 添加适当的注释和文档字符串

### 测试
（待添加测试用例）