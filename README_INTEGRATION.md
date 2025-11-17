# OA系统与RAG系统集成指南

本指南说明如何将RAG知识库系统与OA系统原型界面关联使用。

## 📋 系统架构

```
┌─────────────────┐         HTTP API          ┌──────────────────┐
│  OA系统前端     │ ────────────────────────> │  RAG API服务器    │
│  (HTML/JS)      │ <──────────────────────── │  (Flask)          │
└─────────────────┘         JSON响应           └──────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────────┐
                                              │  RAG服务         │
                                              │  (LlamaIndex +   │
                                              │   LangChain)     │
                                              └──────────────────┘
```

## 🚀 快速开始

### 步骤1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2: 初始化RAG系统

```bash
# 方式1: 使用快速开始脚本（推荐）
python quick_start.py

# 方式2: 分步执行
python -m rag_system.main generate  # 生成文档
python -m rag_system.main index     # 构建索引
```

### 步骤3: 启动API服务器

```bash
python start_rag_server.py
```

服务器将在 `http://localhost:5000` 启动。

### 步骤4: 打开OA系统前端

在浏览器中打开 `design/OA系统原型.html`，即可使用智能问答功能。

## 🔧 配置说明

### API地址配置

如果API服务器运行在不同地址，需要修改 `OA系统原型.html` 中的API配置：

```javascript
// 在 <script> 标签开头找到
const API_BASE_URL = 'http://localhost:5000';
// 修改为你的API服务器地址
```

### CORS配置

如果前端和API服务器不在同一域名，确保Flask已启用CORS（代码中已配置）。

## 📡 API接口说明

### 1. 健康检查

```http
GET /api/health
```

响应：
```json
{
  "status": "ok",
  "service": "RAG QA Service",
  "qa_service_ready": true
}
```

### 2. 问答接口

```http
POST /api/qa
Content-Type: application/json

{
  "question": "差旅费报销的标准是什么？"
}
```

响应：
```json
{
  "success": true,
  "question": "差旅费报销的标准是什么？",
  "answer": "根据《差旅费报销制度 V3.2》...",
  "sources": [
    {
      "document": "差旅费报销制度_V3.2.pdf",
      "excerpt": "国内机票报销上限为经济舱全价票的80%...",
      "score": 0.95
    }
  ]
}
```

## 🎯 功能特性

### 前端集成

1. **智能问答页面** (`qa` 页面)
   - 支持自然语言提问
   - 实时显示AI回答
   - 显示引用来源（文档名 + 段落）

2. **悬浮聊天面板** (`chat-panel`)
   - 快速问答入口
   - 简洁的对话界面
   - 显示引用来源

### 后端服务

1. **RAG检索**
   - 使用LlamaIndex进行向量检索
   - 支持语义相似度搜索
   - 返回top-k相关文档片段

2. **AI生成回答**
   - 使用通义千问生成回答
   - 基于检索到的文档内容
   - 自动引用文档来源

## 🔍 使用示例

### 在OA系统中提问

1. 打开 `OA系统原型.html`
2. 点击"智能问答"卡片或右下角悬浮按钮
3. 输入问题，例如：
   - "差旅费报销的标准是什么？"
   - "报销需要哪些材料？"
   - "报销周期是多久？"
4. 查看AI回答和引用来源

### 测试API

使用curl测试：

```bash
curl -X POST http://localhost:5000/api/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "差旅费报销的标准是什么？"}'
```

## 🐛 常见问题

### Q: 前端无法连接到API？

A: 检查：
1. API服务器是否已启动
2. API地址是否正确（默认 `http://localhost:5000`）
3. 浏览器控制台是否有CORS错误

### Q: 回答显示"服务暂时不可用"？

A: 检查：
1. RAG服务是否已初始化
2. 索引是否已构建
3. API密钥是否正确配置

### Q: 如何修改API端口？

A: 修改 `start_rag_server.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5000, debug=False)
# 改为其他端口，如 8000
```

同时修改前端 `API_BASE_URL`。

## 📝 开发说明

### 添加新功能

1. **扩展API接口**：在 `rag_system/api/flask_api.py` 中添加新路由
2. **修改前端**：在 `OA系统原型.html` 中添加对应的前端逻辑
3. **更新文档**：更新本README

### 自定义回答格式

修改 `OA系统原型.html` 中的 `formatAIResponse` 函数来自定义回答显示格式。

### 添加更多文档

1. 将新文档放入 `./data/documents/` 目录
2. 重新构建索引：`python -m rag_system.main index`

## 🔒 安全建议

1. **生产环境**：
   - 使用HTTPS
   - 添加身份验证
   - 限制API访问频率

2. **API密钥**：
   - 不要将密钥提交到代码仓库
   - 使用环境变量或密钥管理服务

## 📚 相关文档

- [RAG系统详细文档](./README_RAG.md)
- [OA系统设计说明](./design/OA系统原型设计说明.md)

## 🆘 获取帮助

如遇问题，请检查：
1. 日志输出（API服务器和控制台）
2. 浏览器开发者工具（Network和Console）
3. 系统依赖是否完整安装

