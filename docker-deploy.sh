# Docker 构建和部署脚本
# StockWise Docker 容器化部署

echo "🐳 开始 Docker 容器化部署..."

# 1. 构建镜像
echo "📦 构建 Docker 镜像..."
docker build -t stockwise:latest .

# 2. 停止现有容器
echo "🛑 停止现有容器..."
docker stop stockwise 2>/dev/null || true
docker rm stockwise 2>/dev/null || true

# 3. 运行新容器
echo "🚀 启动新容器..."
docker run -d \
  --name stockwise \
  -p 8501:8501 \
  --restart unless-stopped \
  -e CLOVER_API_KEY="${CLOVER_API_KEY}" \
  -e MERCHANT_ID="${MERCHANT_ID}" \
  stockwise:latest

# 4. 检查容器状态
echo "📊 检查容器状态..."
docker ps | grep stockwise

# 5. 显示日志
echo "📝 显示启动日志..."
docker logs stockwise

echo "✅ 部署完成！"
echo "🌐 访问地址: http://localhost:8501"
echo "📊 查看日志: docker logs -f stockwise"
echo "🛑 停止容器: docker stop stockwise"
