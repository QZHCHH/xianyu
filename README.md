# 咸鱼自动化工具

一个全面的咸鱼电商自动化工具，帮助卖家提高效率和销售业绩。

## 功能特点

- **商品管理自动化**：批量上下架、信息更新、爆品采集
- **订单处理自动化**：自动发货、订单状态管理、辅助拍单
- **客户服务自动化**：智能回复、客户关系管理、文案优化
- **平台任务自动化**：日常任务处理、店铺数据分析、自动擦亮
- **内容创作与素材管理**：主图制作、去水印、素材管理
- **多账号管理**：多号发布、发布控制、账号克隆
- **高级营销分析**：热销商品发掘、转化率分析、智能矩阵上架

## 系统要求

- Linux系统（推荐Ubuntu 20.04+）
- Python 3.8+
- MongoDB 4.4+
- Node.js 14+
- Nginx

## 一键部署

1. 登录您的腾讯云服务器
2. 下载部署脚本：
   ```
   curl -O https://raw.githubusercontent.com/your-username/xianyu-tool/master/deploy.sh
   ```
3. 添加执行权限：
   ```
   chmod +x deploy.sh
   ```
4. 以root权限运行脚本：
   ```
   sudo ./deploy.sh
   ```
5. 等待部署完成，按照提示访问系统

## 手动部署

### 后端部署

1. 克隆代码库：
   ```
   git clone https://github.com/your-username/xianyu-tool.git
   cd xianyu-tool
   ```

2. 安装Python依赖：
   ```
   pip install -r requirements.txt
   ```

3. 安装Playwright并下载浏览器：
   ```
   pip install playwright
   python -m playwright install chromium
   ```

4. 初始化数据库：
   ```
   python init_db.py
   ```

5. 启动后端服务：
   ```
   python app.py
   ```

### 前端部署

1. 进入前端目录：
   ```
   cd frontend
   ```

2. 安装依赖：
   ```
   npm install
   ```

3. 构建生产环境版本：
   ```
   npm run build
   ```

4. 配置Nginx（参考deploy.sh中的配置）

## 访问系统

部署完成后，访问 `http://服务器IP` 即可打开系统。

初始管理员账号：
- 用户名：admin
- 密码：admin123

## 安全提示

首次登录后，请立即修改默认密码！

## 许可证

本项目遵循MIT许可证 