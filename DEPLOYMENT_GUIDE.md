# StockWise Enhanced 部署指南

## 🚀 Cloud Run 部署步骤

### 1. 准备 Google Cloud Shell

1. 打开 [Google Cloud Console](https://console.cloud.google.com)
2. 启动 Cloud Shell
3. 克隆代码仓库（如果还没有）

```bash
git clone <your-repository-url>
cd stockwise_final
```

### 2. 设置项目变量

编辑 `deploy-cloudrun-updated.sh` 文件，修改以下变量：

```bash
PROJECT_ID="your-gcp-project-id"  # 替换为你的 GCP 项目 ID
```

### 3. 执行部署

```bash
chmod +x deploy-cloudrun-updated.sh
./deploy-cloudrun-updated.sh
```

脚本会提示你输入：
- Clover API Key
- Merchant ID  
- Gemini API Key (新增)

### 4. 验证部署

部署完成后，脚本会输出应用地址。访问该地址确认应用正常运行。

## 🆕 新功能特性

### 📊 数据可视化
- 销售趋势图表
- 热销商品排行
- 销售额占比饼图
- 每日销售趋势

### 🚨 库存预警系统
- 低库存提醒
- 缺货预警
- 无销量商品提醒
- 预警报告导出

### 📈 销售趋势分析
- 月环比分析
- 年同比分析
- 趋势方向判断
- 增长率计算

### 🌍 多语言支持
- 中文/英文切换
- 界面语言自适应
- 实时语言切换

### 📱 移动端优化
- 响应式设计
- 触摸友好界面
- 移动端布局优化

### 🤖 AI 智能功能 (新增)
- **智能商品分类**: 使用 Gemini API 自动分类商品
  - 主类别识别 (生鲜、日用品、零食等)
  - 子类别细分 (蔬菜、水果、肉类等)
  - 商品属性标注 (有机、进口、本地等)
  - 目标客户分析
  - 存储要求建议

- **智能描述生成**: AI 生成营销描述
  - 多种长度选择 (简短/中等/详细)
  - 突出商品特色和卖点
  - 生成关键词和使用建议
  - 营销导向的文案

- **批量 AI 处理**: 
  - 批量商品分类
  - 批量描述生成
  - 进度跟踪和结果导出

- **分类统计分析**:
  - 主类别分布图表
  - 子类别统计
  - 分类置信度分析

## 🔧 配置说明

### 环境变量
- `CLOVER_API_KEY`: Clover API 访问密钥
- `MERCHANT_ID`: 商户 ID
- `GEMINI_API_KEY`: Gemini AI API 密钥 (新增)

### 资源配置
- 内存: 1GB
- CPU: 1核心
- 最大实例: 10
- 最小实例: 0（冷启动）
- 超时: 300秒

## 🐛 故障排除

### 常见问题

**Q: 部署失败，内存不足**
```
A: 在部署命令中增加 --memory 2Gi 参数
```

**Q: 应用启动缓慢**
```
A: 设置 --min-instances 1 保持热启动
```

**Q: API 调用失败**
```
A: 检查环境变量设置和网络连接
```

### 查看日志
```bash
gcloud logs tail stockwise-enhanced --platform managed --region us-central1
```

### 更新部署
重新运行部署脚本即可更新应用。

## 📞 支持

如有问题，请检查：
1. GCP 项目配置
2. API 密钥有效性
3. 网络连接状态
4. Cloud Run 服务状态

---

**Copyright © 2026 EasternMarket. All rights reserved.**
