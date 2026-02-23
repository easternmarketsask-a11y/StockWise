# StockWise - EasternMarket 商品销量查询系统

<div align="center">

![StockWise Logo](https://img.shields.io/badge/StockWise-EasternMarket-blue?style=for-the-badge)

**一个基于 Streamlit 的 Clover POS 销量数据分析工具**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-2.2.0-orange.svg)](https://pandas.pydata.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

## 📋 项目简介

StockWise 是专为 EasternMarket 设计的商品销量查询和分析系统。通过集成 Clover POS API，提供实时库存同步、精准销量分析和数据导出功能，帮助商家快速了解商品销售情况。

### ✨ 核心功能

- 🔍 **智能销量查询**：支持按商品名称、SKU、Code 或条码进行搜索
- 📊 **日期范围分析**：灵活选择时间段进行销量统计
- 📦 **全店报表导出**：一键导出近30天全店销售数据为 CSV 格式
- 🔄 **实时数据同步**：自动从 Clover POS 获取最新库存和销售数据
- 📈 **可视化展示**：清晰的表格和指标展示销售业绩

## 🏗️ 技术架构

### 技术栈
- **前端框架**：Streamlit 1.31.0
- **数据处理**：Pandas 2.2.0
- **HTTP 请求**：Requests 2.31.0
- **API 集成**：Clover POS REST API v3

### 架构设计
```
stockwise_final/
├── main.py          # 主程序入口和业务逻辑控制
├── api_handler.py   # Clover API 调用处理层
├── data_engine.py   # 数据审计和报表处理引擎
├── ui_render.py     # UI 样式和页面渲染组件
├── requirements.txt # Python 依赖包列表
└── .env.example     # 环境变量配置模板
```

### MVC 架构模式
- **Model**：`data_engine.py` - 数据处理和业务逻辑
- **View**：`ui_render.py` - 用户界面渲染
- **Controller**：`main.py` + `api_handler.py` - 流程控制和API集成

## 🚀 快速开始

### 环境要求
- Python 3.9 或更高版本
- pip 包管理器
- Clover POS API 访问权限

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd StockWise/stockwise_final
```

2. **创建虚拟环境**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 Clover API 信息
CLOVER_API_KEY=your_clover_api_key_here
MERCHANT_ID=your_merchant_id_here
```

5. **启动应用**
```bash
streamlit run main.py
```

应用将在浏览器中打开：`http://localhost:8501`

## ⚙️ 配置说明

### Clover API 配置
在 `.env` 文件中配置以下参数：

```env
# 必需配置
CLOVER_API_KEY=your_clover_api_key_here    # Clover API 访问密钥
MERCHANT_ID=your_merchant_id_here          # 商户 ID

# 可选配置
API_TIMEOUT=30                              # API 请求超时时间（秒）
CACHE_TTL=1800                              # 数据缓存时间（秒）
```

### 获取 Clover API 密钥
1. 登录 [Clover Developer Portal](https://dev.clover.com)
2. 创建新应用或选择现有应用
3. 获取 API Key 和 Merchant ID
4. 确保应用具有必要的权限：
   - 读取商品信息 (`items:r`)
   - 读取订单信息 (`orders:r`)

## 📖 使用指南

### 销量分析查询
1. 在主界面选择日期范围（开始日期和结束日期）
2. 输入搜索关键词（支持商品名称、SKU、Code 或条码）
3. 点击"查询"按钮开始分析
4. 查看结果：销量汇总、详细数据表格

### 全店报表导出
1. 点击"导出近30天全店销售产品 CSV"按钮
2. 系统将自动同步全店销售流水
3. 生成 CSV 文件供下载
4. 文件命名格式：`Sales_Summary_MMDD.csv`

### 数据字段说明
- **商品信息**：商品名称
- **售价**：商品单价（美元）
- **区间销量**：选定时间段内的销售数量
- **销售总额**：选定时间段内的销售金额
- **标识符**：商品 SKU 或 Code

## 🔧 开发指南

### 项目结构
```
stockwise_final/
├── main.py              # 主程序入口
│   ├── 页面配置
│   ├── 业务流程控制
│   └── 用户交互处理
├── api_handler.py       # API 处理层
│   ├── CloverAPIHandler 类
│   ├── 库存数据获取
│   └── 销售数据获取
├── data_engine.py       # 数据处理引擎
│   ├── DataEngine 类
│   ├── 销量审计逻辑
│   └── 报表生成逻辑
└── ui_render.py         # UI 渲染组件
    ├── UIRenderer 类
    ├── 样式定义
    └── 页面组件
```

### 核心类说明

#### CloverAPIHandler
- `fetch_full_inventory()`: 获取完整库存列表
- `fetch_targeted_sales()`: 获取指定商品的销售数据
- `fetch_full_period_sales()`: 获取全店销售数据

#### DataEngine
- `audit_process()`: 执行销量审计和分析
- `prepare_export_csv()`: 准备 CSV 导出数据

#### UIRenderer
- `apply_style()`: 应用自定义 CSS 样式
- `render_header()`: 渲染页面头部
- `render_custom_footer()`: 渲染页面底部

### 扩展开发
如需添加新功能，请遵循以下原则：
1. 保持 MVC 架构分离
2. 在相应模块中添加功能
3. 更新配置文件和文档
4. 进行充分测试

## 🐛 故障排除

### 常见问题

**Q: 应用启动失败**
```
A: 检查 Python 版本和依赖安装
   - 确保 Python 3.9+
   - 重新安装依赖：pip install -r requirements.txt
```

**Q: API 调用失败**
```
A: 检查 API 配置和网络连接
   - 验证 CLOVER_API_KEY 和 MERCHANT_ID
   - 检查网络连接和防火墙设置
   - 确认 API 权限配置
```

**Q: 数据加载缓慢**
```
A: 优化数据请求和缓存
   - 调整 CACHE_TTL 设置
   - 检查 API_TIMEOUT 配置
   - 考虑数据量大小
```

**Q: 虚拟环境问题**
```
A: 重新创建虚拟环境
   - 删除 .venv 文件夹
   - 重新执行 python -m venv .venv
   - 重新安装依赖
```

### 日志调试
启用详细日志：
```bash
streamlit run main.py --logger.level debug
```

## 📝 更新日志

### v1.4.2-STABLE (当前版本)
- ✅ 优化跨年数据查询逻辑
- ✅ 增强手动 ID 链接机制
- ✅ 改进错误处理和用户体验
- ✅ 完善文档和配置模板

### 计划更新
- 🔄 添加图表可视化功能
- 🔄 支持多商户管理
- 🔄 增加数据导出格式选择
- 🔄 优化移动端显示

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与联系

如有问题或建议，请通过以下方式联系：

- 📧 邮箱：support@easternmarket.com
- 🐛 问题反馈：[GitHub Issues](https://github.com/your-repo/issues)
- 📖 文档：[项目 Wiki](https://github.com/your-repo/wiki)

---

<div align="center">

**Copyright © 2026 EasternMarket. All rights reserved.**

Made with ❤️ for EasternMarket

</div>
