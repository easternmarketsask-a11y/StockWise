# StockWise 应用 Dockerfile (支持 Streamlit)
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

# 检查是否为 Streamlit 模式
ARG APP_MODE=streamlit

# 根据模式选择启动命令
RUN echo "#!/bin/bash" > /app/entrypoint.sh && \
    echo "if [ \"\$APP_MODE\" = \"streamlit\" ]; then" >> /app/entrypoint.sh && \
    echo "    echo '🚀 启动 Streamlit 应用...'" >> /app/entrypoint.sh && \
    echo "    exec streamlit run main.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false" >> /app/entrypoint.sh && \
    echo "else" >> /app/entrypoint.sh && \
    echo "    echo '🚀 启动 FastAPI 应用...'" >> /app/entrypoint.sh && \
    echo "    exec uvicorn simple_app:app --host 0.0.0.0 --port 8080" >> /app/entrypoint.sh && \
    echo "fi" >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
