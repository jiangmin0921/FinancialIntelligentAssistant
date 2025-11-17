# 快速开始指南

## 首次运行步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行快速开始脚本

```bash
python quick_start.py
```

这个脚本会：
1. ✅ 检查依赖
2. ✅ 创建目录结构
3. ✅ 生成财务文档（PDF和Word）
4. ✅ **构建向量索引**（这一步需要时间）

### 3. 关于"索引不存在"的提示

**这是正常的！** 首次运行时，你会看到：

```
⚠ 索引不存在，需要先构建索引
  错误: 索引不存在，请先构建索引。路径: data\vector_store\chroma_db
```

**这是预期行为**，因为：
- 这是第一次运行，索引还没有构建
- 脚本接下来会自动构建索引
- 构建完成后，索引会保存在 `data/vector_store/chroma_db/` 目录

### 4. 构建索引过程

构建索引时，你会看到：

```
正在加载本地embedding模型: BAAI/bge-small-zh-v1.5
（首次运行需要下载模型，请耐心等待...）
使用镜像源: https://hf-mirror.com
✓ 本地embedding模型加载成功

正在从 data/documents 读取文档...
已加载 X 个文档
正在构建索引...
[进度条显示]
索引构建完成！
✓ 索引构建并保存成功
```

### 5. 验证索引

构建完成后，可以检查索引状态：

```bash
python check_index.py
```

应该看到：
```
[OK] 索引目录存在
[OK] ChromaDB集合存在
  集合名称: financial_knowledge
  向量数量: XXX
[OK] 索引状态正常
```

### 6. 启动API服务器

索引构建完成后，启动API服务器：

```bash
python start_rag_server.py
```

### 7. 使用OA系统

在浏览器中打开 `design/OA系统原型.html`，开始使用智能问答功能。

## 常见问题

### Q: 看到"索引不存在"错误怎么办？

A: 这是正常的！继续运行脚本，它会自动构建索引。

### Q: 索引构建失败怎么办？

A: 检查：
1. 文档是否已生成（`data/documents/` 目录是否有文件）
2. 网络连接（下载embedding模型需要网络）
3. 依赖包是否完整安装

### Q: 如何重新构建索引？

A: 删除索引目录后重新运行：

```bash
# Windows PowerShell
Remove-Item -Recurse -Force .\data\vector_store\chroma_db

# 然后重新运行
python quick_start.py
```

### Q: 索引构建需要多长时间？

A: 取决于：
- 文档数量（通常1-2分钟）
- 网络速度（首次下载embedding模型）
- 计算机性能

通常首次运行需要3-5分钟，后续运行会更快。

## 完整流程示例

```bash
# 1. 安装依赖（首次）
pip install -r requirements.txt

# 2. 快速开始（生成文档+构建索引）
python quick_start.py

# 3. 启动API服务器
python start_rag_server.py

# 4. 打开浏览器
# 访问 design/OA系统原型.html
```

## 提示

- ✅ 首次运行会下载embedding模型（约100MB），请耐心等待
- ✅ 如果网络慢，可以设置镜像源：`$env:HF_ENDPOINT="https://hf-mirror.com"`
- ✅ 索引构建完成后，后续启动会很快（只需加载索引）

