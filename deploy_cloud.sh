#!/bin/bash

# StockWise 云服务器部署脚本
# 适用于 Ubuntu 20.04+ / CentOS 8+

echo "🚀 开始部署 StockWise 到云服务器..."

# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Python 和 pip
sudo apt install python3 python3-pip python3-venv -y

# 3. 创建项目目录
mkdir -p /opt/stockwise
cd /opt/stockwise

# 4. 上传项目文件 (需要手动上传)
echo "请将以下文件上传到 /opt/stockwise/ 目录："
echo "- main.py"
echo "- api_handler.py" 
echo "- data_engine.py"
echo "- ui_render.py"
echo "- requirements.txt"
echo "- .env"

# 5. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt
pip install python-dotenv

# 7. 创建 systemd 服务
sudo tee /etc/systemd/system/stockwise.service > /dev/null <<EOF
[Unit]
Description=StockWise Streamlit App
After=network.target

[Service]
User=root
WorkingDirectory=/opt/stockwise
Environment=PATH=/opt/stockwise/.venv/bin
ExecStart=/opt/stockwise/.venv/bin/streamlit run main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 8. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable stockwise
sudo systemctl start stockwise

# 9. 检查状态
sudo systemctl status stockwise

echo "✅ 部署完成！"
echo "🌐 访问地址: http://你的服务器IP:8501"
echo "📝 查看日志: sudo journalctl -u stockwise -f"
