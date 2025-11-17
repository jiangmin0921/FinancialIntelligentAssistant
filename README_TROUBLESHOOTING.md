# 故障排除指南

## 网络超时问题

### 问题：下载模型时出现连接超时

```
Connection to huggingface.co timed out
```

### 解决方案

#### 方法1: 使用镜像源（推荐）

**Windows PowerShell:**
```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
python quick_start.py
```

**Windows CMD:**
```cmd
set HF_ENDPOINT=https://hf-mirror.com
python quick_start.py
```

**Linux/Mac:**
```bash
export HF_ENDPOINT=https://hf-mirror.com
python quick_start.py
```

#### 方法2: 永久设置环境变量

**Windows:**
1. 右键"此电脑" -> 属性 -> 高级系统设置
2. 环境变量 -> 新建系统变量
3. 变量名: `HF_ENDPOINT`
4. 变量值: `https://hf-mirror.com`

**Linux/Mac:**
添加到 `~/.bashrc` 或 `~/.zshrc`:
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

#### 方法3: 手动下载模型

```bash
# 安装huggingface-hub
pip install huggingface-hub

# 设置镜像源
set HF_ENDPOINT=https://hf-mirror.com  # Windows
# 或
export HF_ENDPOINT=https://hf-mirror.com  # Linux/Mac

# 下载模型
huggingface-cli download BAAI/bge-small-zh-v1.5
```

#### 方法4: 使用更小的模型

如果网络实在不行，可以修改 `config.yaml` 使用更小的模型：

```yaml
models:
  embedding:
    provider: "local"
    model_name: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 更小的模型
```

## 其他常见问题

### 问题1: 导入错误

```
cannot import name 'HuggingFaceEmbedding'
```

**解决:**
```bash
pip install llama-index-embeddings-huggingface
```

### 问题2: 内存不足

如果模型下载后加载失败，可能是内存不足。

**解决:**
- 使用更小的模型
- 关闭其他程序释放内存
- 增加虚拟内存

### 问题3: API超时

如果使用OpenAI API时超时。

**解决:**
- 切换到本地模型（修改config.yaml）
- 检查网络连接
- 增加超时时间

## 快速诊断

运行诊断脚本：

```bash
python -c "
import sys
print('Python版本:', sys.version)

try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    print('✓ HuggingFaceEmbedding 导入成功')
except Exception as e:
    print('✗ HuggingFaceEmbedding 导入失败:', e)

try:
    import sentence_transformers
    print('✓ sentence-transformers 已安装')
except:
    print('✗ sentence-transformers 未安装')

import os
hf_endpoint = os.getenv('HF_ENDPOINT', '未设置')
print('HF_ENDPOINT:', hf_endpoint)
"
```

## 获取帮助

如果以上方法都无法解决问题，请：

1. 检查Python版本（需要3.10+）
2. 检查所有依赖是否已安装
3. 查看完整错误信息
4. 检查网络连接和防火墙设置

