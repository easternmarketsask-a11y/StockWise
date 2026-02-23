# 使用官方 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

# 复制应用文件
COPY . .

# 暴露端口
EXPOSE 8501

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
