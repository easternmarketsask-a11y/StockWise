# StockWise FastAPI 应用 Dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PORT=8080
ENV PYTHONPATH=/app

# 启动 FastAPI 应用
CMD ["uvicorn", "simple_app:app", "--host", "0.0.0.0", "--port", "8080"]
