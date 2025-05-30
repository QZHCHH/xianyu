# XIANYU-TOOL-AUTO 咸鱼自动化工具

咸鱼自动化工具是一款专为闲鱼卖家设计的自动化管理平台，帮助卖家高效管理商品、订单、客户服务等各方面工作，提升运营效率和销售转化率。

## 主要功能

### 1. 商品管理
- 商品批量发布与管理
- 商品库存与价格调整
- 商品热销分析与推荐

### 2. 订单处理
- 订单自动化处理
- 物流单号生成与跟踪
- 订单数据统计与分析

### 3. 内容创作与素材管理
- 商品主图快速制作
- 图片去水印处理
- 素材库管理
- 商品描述自动生成

### 4. 多账号管理
- 多号统一管理
- 发布频率控制
- 账号克隆（子母号）
- 商品同步功能

### 5. 客户服务自动化
- 自动回复系统
- 客户关系管理
- 文案优化功能
- 流量密码生成

### 6. 平台任务自动化
- 日常任务处理
- 店铺数据分析
- 自动擦亮功能
- 发布地区优化

### 7. 高级营销分析
- 热销商品发掘
- 转化率分析
- 智能矩阵上架

## 技术架构

- 后端：Python Flask API
- 数据库：MongoDB
- 前端：Vue.js (前端代码在frontend目录)

## 安装与部署

### 前提条件
- Python 3.8+
- MongoDB 4.4+
- Node.js 14+ (仅前端开发需要)

### 安装步骤

1. 克隆代码库
```bash
git clone https://github.com/your-username/xianyu-tool-auto.git
cd xianyu-tool-auto
```

2. 安装后端依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
```bash
python init_db.py
```

4. 启动后端服务
```bash
python app.py
```

5. 安装并启动前端（开发模式）
```bash
cd frontend
npm install
npm run serve
```

### 使用Docker部署

```bash
docker-compose up -d
```

## API文档

API文档请参考 [API.md](API.md) 文件。

## 目录结构

```
xianyu-tool-auto/
├── app.py              # 主应用入口
├── init_db.py          # 数据库初始化脚本
├── deploy.sh           # 部署脚本
├── requirements.txt    # Python依赖
├── modules/            # 功能模块
│   ├── product_manager.py     # 商品管理模块
│   ├── order_processor.py     # 订单处理模块
│   ├── content_creator.py     # 内容创作模块
│   ├── account_manager.py     # 多账号管理模块
│   ├── customer_service.py    # 客户服务模块
│   ├── platform_tasks.py      # 平台任务模块
│   └── marketing_analyzer.py  # 营销分析模块
├── data/               # 数据文件
│   └── ecommerce_dict.txt     # 电商词典
├── static/             # 静态资源
│   ├── materials/      # 素材存储
│   └── processed/      # 处理后图片存储
├── logs/               # 日志目录
└── frontend/           # 前端代码
```

## 许可证

MIT

## 联系方式

如有问题，请联系开发者邮箱：developer@example.com 