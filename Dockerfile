# Google Cloud Run 部署专用 Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 暴露 Cloud Run 默认端口
EXPOSE 8080

# 设置环境变量
ENV PORT=8080
ENV PYTHONPATH=/app

# 启动命令 - 监听 Cloud Run 端口
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
