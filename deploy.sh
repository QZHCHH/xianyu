#!/bin/bash

echo "===== Xianyu Automation Tool Deployment Script ====="
echo "===== 咸鱼自动化工具一键部署脚本 ====="
echo "Checking system environment... (正在检查系统环境...)"

# Check if running as root (检查是否为root用户)
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with root privileges (请使用root权限运行此脚本)"
  exit 1
fi

# Set working directory (设置工作目录)
WORK_DIR="/opt/xianyu-tool"
mkdir -p $WORK_DIR
cd $WORK_DIR

# Detect OS type (检测操作系统类型)
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
else
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
fi

echo "Detected OS: $OS (检测到的操作系统: $OS)"

# Update system and install dependencies (更新系统并安装基础依赖)
echo "Updating system and installing dependencies... (正在更新系统并安装基础依赖...)"
if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
    apt-get update -y
    apt-get install -y git curl wget nginx python3 python3-pip nodejs npm
elif [[ "$OS" == "centos" || "$OS" == "rhel" || "$OS" == "fedora" ]]; then
    yum update -y
    yum install -y epel-release
    yum install -y git curl wget nginx python3 python3-pip
    
    # Install Node.js on CentOS
    if ! command -v node &> /dev/null; then
        echo "Installing Node.js and npm... (正在安装Node.js和npm...)"
        curl -sL https://rpm.nodesource.com/setup_16.x | bash -
        yum install -y nodejs
    fi
else
    echo "Unsupported OS: $OS (不支持的操作系统: $OS)"
    exit 1
fi

# Install MongoDB (安装MongoDB)
echo "Installing MongoDB... (正在安装MongoDB...)"
if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
    # Ubuntu/Debian installation
    wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    apt-get update
    apt-get install -y mongodb-org
    systemctl enable mongod
    systemctl start mongod
elif [[ "$OS" == "centos" || "$OS" == "rhel" || "$OS" == "fedora" ]]; then
    # CentOS/RHEL installation
    cat > /etc/yum.repos.d/mongodb-org-4.4.repo << EOF
[mongodb-org-4.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/4.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
EOF
    yum install -y mongodb-org
    systemctl enable mongod
    systemctl start mongod
fi

# Clone project code (克隆项目代码)
echo "Cloning project code... (正在克隆项目代码...)"
git clone https://github.com/your-username/xianyu-tool.git .

# Install Python dependencies (安装Python依赖)
echo "Installing Python dependencies... (正在安装Python依赖...)"
pip3 install -r requirements.txt
pip3 install playwright
python3 -m playwright install chromium

# Install frontend dependencies and build (安装前端依赖并构建)
echo "Installing frontend dependencies and building... (正在安装前端依赖并构建...)"
cd frontend
npm install
npm run build
cd ..

# Configure Nginx (配置Nginx)
echo "Configuring Nginx... (正在配置Nginx...)"
if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
    # Ubuntu/Debian configuration
    cat > /etc/nginx/sites-available/xianyu-tool <<EOF
server {
    listen 80;
    server_name _;

    location / {
        root $WORK_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF
    ln -sf /etc/nginx/sites-available/xianyu-tool /etc/nginx/sites-enabled/
elif [[ "$OS" == "centos" || "$OS" == "rhel" || "$OS" == "fedora" ]]; then
    # CentOS/RHEL configuration
    cat > /etc/nginx/conf.d/xianyu-tool.conf <<EOF
server {
    listen 80;
    server_name _;

    location / {
        root $WORK_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF
fi

# Test and restart Nginx (测试并重启Nginx)
nginx -t
systemctl restart nginx

# Setup backend service (设置后端服务)
echo "Setting up backend service... (正在设置后端服务...)"
cat > /etc/systemd/system/xianyu-backend.service <<EOF
[Unit]
Description=Xianyu Automation Tool Backend
After=network.target

[Service]
User=root
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/python3 app.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xianyu-backend
systemctl start xianyu-backend

# Initialize database (初始化数据库)
echo "Initializing database... (正在初始化数据库...)"
python3 init_db.py

# Configure firewall (设置防火墙)
echo "Configuring firewall... (正在配置防火墙...)"
if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
    # Ubuntu/Debian firewall
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 22/tcp
    fi
elif [[ "$OS" == "centos" || "$OS" == "rhel" || "$OS" == "fedora" ]]; then
    # CentOS/RHEL firewall
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --reload
    fi
fi

# Completed (完成)
echo "===== Deployment Completed ====="
echo "===== 部署完成 ====="
echo "You can access Xianyu Automation Tool at http://YOUR_SERVER_IP"
echo "您可以通过 http://服务器IP 访问咸鱼自动化工具"
echo "Default admin account: admin (默认管理员账号: admin)"
echo "Default admin password: admin123 (默认管理员密码: admin123)"
echo "Please change your password immediately after login! (请登录后立即修改密码!)" 