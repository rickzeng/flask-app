# A股股票数据获取模块

本模块为Flask应用添加了A股股票数据获取功能，包括实时股价、资金流向分析等。

## 功能特性

1. **获取A股股票数据** - 支持获取股票基本信息、实时价格等
2. **获取最近五天资金量流入前10的股票** - 分析主力资金流向，找出热门股票
3. **支持数据缓存** - 内置缓存机制，减少API请求次数
4. **提供RESTful API接口** - 标准化的API接口设计
5. **集成到现有Flask应用** - 无缝集成现有系统
6. **添加错误处理和日志** - 完善的错误处理和日志记录
7. **创建相应的测试用例** - 完整的单元测试和集成测试

## API接口

### 1. 股票模块健康检查
```
GET /api/stocks/health
```

### 2. 获取股票基本信息
```
GET /api/stocks/info/{stock_code}
```

### 3. 获取股票资金流向
```
GET /api/stocks/flow/{stock_code}?days=5
```

### 4. 获取资金流入前N的股票
```
GET /api/stocks/top-fund-flow?days=5&limit=10
```

### 5. 清空缓存
```
POST /api/stocks/cache/clear
```

## 使用示例

1. 获取平安银行(000001)的基本信息:
```
GET /api/stocks/info/000001
```

2. 获取万科A(000002)最近5天的资金流向:
```
GET /api/stocks/flow/000002?days=5
```

3. 获取最近5天资金流入前10的股票:
```
GET /api/stocks/top-fund-flow?days=5&limit=10
```

## 测试

运行测试用例:
```bash
source venv/bin/activate
python -m pytest tests/test_stock_service.py -v
python -m pytest tests/test_stock_routes.py -v
```

## 配置

在config.py中添加了以下股票数据相关配置:
- STOCK_CACHE_TIMEOUT: 缓存超时时间(秒)
- STOCK_API_TIMEOUT: API请求超时时间(秒)

## 架构

- app/stock_service.py: 股票数据服务核心逻辑
- app/stock_routes.py: API路由定义
- tests/test_stock_service.py: 股票服务单元测试
- tests/test_stock_routes.py: API路由测试