# 财务助手 - 知识库 & RAG 系统

基于 LlamaIndex + LangChain 构建的企业财务知识库检索问答系统。

## 📋 项目结构

```
FinancialIntelligentAssistant/
├── rag_system/                  # RAG系统核心模块
│   ├── data_generator/         # 数据生成模块
│   │   └── generate_docs.py    # 自动生成PDF/Word文档
│   ├── indexer/                # 索引模块
│   │   └── llama_indexer.py   # LlamaIndex索引和检索
│   ├── agent/                  # Agent编排模块
│   │   └── langchain_agent.py # LangChain Agent
│   ├── retriever/              # 检索模块
│   │   └── rag_retriever.py   # RAG检索器
│   ├── api/                    # API接口
│   │   └── qa_api.py          # 问答API
│   └── main.py                 # 主程序入口
├── config.yaml                 # 配置文件
├── requirements.txt            # 依赖包
└── README_RAG.md              # 本文档
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- 建议使用虚拟环境

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

编辑 `config.yaml` 文件，设置API密钥：

```yaml
models:
  embedding:
    api_key: "your-openai-api-key"  # 或使用本地模型
  llm:
    api_key: "your-dashscope-api-key"  # 通义千问API Key
```

或者设置环境变量：

```bash
export OPENAI_API_KEY="your-key"
export DASHSCOPE_API_KEY="your-key"
```

### 4. 使用流程

#### 步骤1: 生成文档

自动生成企业财务文档（PDF和Word格式）：

```bash
python -m rag_system.main generate
```

生成的文档会保存在 `./data/generated/` 目录，并自动复制到 `./data/documents/` 目录。

#### 步骤2: 构建索引

使用LlamaIndex构建向量索引：

```bash
python -m rag_system.main index
```

索引会保存在 `./data/vector_store/` 目录。

#### 步骤3: 问答

启动交互式问答：

```bash
python -m rag_system.main qa
```

## 🏗️ 技术架构

### 1. 数据准备

- **文档格式**: PDF、Word
- **文档类型**: 财务制度、技术文档、FAQ
- **生成方式**: 自动模拟生成企业财务文档

### 2. 框架选择

- **索引 & 检索**: LlamaIndex
- **Agent编排**: LangChain
- **向量库**: ChromaDB（开箱即用）

### 3. Chunk策略

支持三种切分策略（在 `config.yaml` 中配置）：

- **semantic**: 按语义切分（推荐，默认）
- **page**: 按页切分
- **title**: 按标题切分

### 4. Embedding模型

- **默认**: OpenAI text-embedding-3-small
- **中文优化**: BAAI/bge-small-zh-v1.5（本地模型）
- **配置**: 在 `config.yaml` 中设置

### 5. LLM模型

- **默认**: 通义千问（qwen-turbo）
- **备选**: OpenAI兼容接口
- **配置**: 在 `config.yaml` 中设置

## 📝 功能特性

### ✅ 已实现功能

1. **文档生成**
   - 自动生成PDF格式财务文档
   - 自动生成Word格式财务文档
   - 包含差旅费报销制度、财务管理制度、FAQ等

2. **索引构建**
   - 使用LlamaIndex构建向量索引
   - 支持多种chunk策略
   - 持久化存储（ChromaDB）

3. **检索问答**
   - 自然语言问题输入
   - 相关文档片段检索
   - 大模型生成回答
   - **支持中文问答**
   - **提供引用来源**（文档名 + 段落）

4. **Agent编排**
   - LangChain Agent框架
   - 简化版RAG Agent（不依赖复杂Agent）

## 🔧 配置说明

### config.yaml 主要配置项

```yaml
# 模型配置
models:
  embedding:
    provider: "openai"  # 或使用本地模型
    model_name: "text-embedding-3-small"
  
  llm:
    provider: "tongyi"  # 通义千问
    model_name: "qwen-turbo"

# 向量库配置
vector_store:
  type: "chroma"
  persist_dir: "./data/vector_store"

# 文档处理配置
document:
  chunk_strategy: "semantic"  # semantic/page/title
  chunk_size: 512
  chunk_overlap: 50

# RAG配置
rag:
  top_k: 3  # 检索top-k个相关文档片段
  similarity_threshold: 0.7
```

## 📖 使用示例

### Python代码示例

```python
from rag_system.api.qa_api import QAService

# 初始化服务
qa_service = QAService()

# 提问
result = qa_service.ask("差旅费报销的标准是什么？")

# 获取回答
print(result['answer'])

# 查看引用来源
for source in result['sources']:
    print(f"来源: {source['document']}")
    print(f"摘要: {source['excerpt']}")
```

### 命令行示例

```bash
# 生成文档
python -m rag_system.main generate

# 构建索引
python -m rag_system.main index

# 问答
python -m rag_system.main qa
```

## 🎯 设计说明

### Chunk策略选择

- **semantic（语义切分）**: 
  - 优点：保持语义完整性，检索准确度高
  - 适用：长文档、结构化文档
  - 实现：使用SemanticSplitterNodeParser

- **page（按页切分）**:
  - 优点：简单直接，易于定位
  - 适用：PDF文档，需要精确页码引用
  - 实现：使用SentenceSplitter

- **title（按标题切分）**:
  - 优点：按章节组织，结构清晰
  - 适用：有明确章节结构的文档
  - 实现：使用SentenceSplitter + 标题识别

### Embedding模型选择

- **OpenAI text-embedding-3-small**: 
  - 优点：性能好，支持多语言
  - 缺点：需要API调用，有成本

- **BAAI/bge-small-zh-v1.5**:
  - 优点：免费，中文优化，可本地运行
  - 缺点：需要下载模型，占用空间

### 向量库选择

- **ChromaDB**: 
  - 开箱即用，无需额外配置
  - 支持持久化存储
  - 适合中小规模知识库

## 🔍 引用来源格式

系统会在回答中提供引用来源，格式如下：

```
回答：根据[来源1: 差旅费报销制度_V3.2.pdf]...

引用来源：
  [1] 差旅费报销制度_V3.2.pdf
      国内机票报销上限为经济舱全价票的80%...
  [2] 财务FAQ.pdf
      报销周期为每月1-10日受理上月单据...
```

## ⚠️ 注意事项

1. **API密钥**: 需要配置OpenAI或通义千问的API密钥
2. **模型下载**: 如果使用本地embedding模型，首次运行会自动下载
3. **内存要求**: 使用本地模型需要较大内存（建议8GB+）
4. **文档格式**: 确保PDF/Word文档格式正确，避免解析错误

## 🐛 常见问题

### Q: 索引构建失败？
A: 检查文档目录是否存在，文档格式是否正确。

### Q: 问答没有返回结果？
A: 确认索引已构建，检查API密钥是否正确配置。

### Q: 中文回答效果不好？
A: 尝试使用中文优化的embedding模型（如bge-small-zh-v1.5）。

### Q: 如何添加自己的文档？
A: 将文档放入 `./data/documents/` 目录，重新构建索引。

## 📚 扩展开发

### 添加新的文档类型

修改 `rag_system/data_generator/generate_docs.py`，添加新的文档生成逻辑。

### 自定义检索策略

修改 `rag_system/indexer/llama_indexer.py`，调整检索参数。

### 集成到Web应用

使用 `rag_system/api/qa_api.py` 中的 `QAService` 类，可以轻松集成到Flask/FastAPI等Web框架。

## 📄 许可证

本项目仅供学习和研究使用。

## 👥 贡献

欢迎提交Issue和Pull Request！

