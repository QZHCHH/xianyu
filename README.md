# 咸鱼自动化工具

基于需求分析文档开发的咸鱼平台自动化工具，包含商品管理、订单处理、客户服务等多个自动化模块。

## 功能特点

- 商品管理自动化：批量上下架、商品信息更新、爆品采集等
- 订单处理自动化：自动发货、订单状态管理等
- 客户服务自动化：自动回复系统、客户关系管理等
- 平台任务自动化：日常任务处理、店铺数据分析等
- 内容创作与素材管理：主图制作、去水印、素材管理等
- 多账号管理：多号发布、账号克隆等
- 高级营销分析：热销商品发掘、转化率分析等

## 技术栈

- 后端：Python + Flask + MongoDB
- 前端：Vue.js + Element UI
- 自动化：Playwright

## 安装部署

### 系统要求

- 操作系统：Ubuntu/Debian 或 CentOS/RHEL
- Python 3.7+
- Node.js 12+
- MongoDB 4.4+

### 一键部署

使用部署脚本进行快速部署：

```bash
sudo bash deploy.sh
```

### 手动部署

1. 安装依赖

```bash
# 安装Python依赖
pip3 install -r requirements.txt
pip3 install playwright
python3 -m playwright install chromium

# 安装前端依赖并构建
cd frontend
npm install
npm run build
cd ..
```

2. 配置数据库

```bash
python3 init_db.py
```

3. 启动服务

```bash
python3 app.py
```

## 使用说明

1. 访问 http://服务器IP 打开系统
2. 默认管理员账号：admin
3. 默认管理员密码：admin123
4. 登录后请立即修改密码

## 开发团队

- 产品设计：XXX
- 前端开发：XXX
- 后端开发：XXX
- 测试与部署：XXX

## 许可证

MIT License 