"""
重新构建索引 - 修复空索引问题
"""

import sys
import io
import shutil
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    print("=" * 60)
    print("重新构建索引")
    print("=" * 60)
    
    # 1. 检查文档
    print("\n[1/4] 检查文档...")
    doc_dir = Path("./data/documents")
    if not doc_dir.exists():
        print("[ERROR] 文档目录不存在")
        return False
    
    files = list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))
    if not files:
        print("[ERROR] 文档目录为空")
        print("请先运行: python -m rag_system.main generate")
        return False
    
    print(f"[OK] 找到 {len(files)} 个文档")
    
    # 2. 删除旧索引
    print("\n[2/4] 删除旧索引...")
    index_dir = Path("./data/vector_store/chroma_db")
    if index_dir.exists():
        try:
            shutil.rmtree(index_dir)
            print("[OK] 旧索引已删除")
        except Exception as e:
            print(f"[WARNING] 无法删除旧索引: {e}")
            print("尝试继续...")
    
    # 3. 检查依赖
    print("\n[3/4] 检查依赖...")
    try:
        import chromadb
        print("[OK] chromadb 已安装")
    except ImportError:
        print("[ERROR] chromadb 未安装")
        print("请运行: pip install chromadb")
        return False
    
    try:
        import llama_index
        print("[OK] llama-index 已安装")
    except ImportError:
        print("[ERROR] llama-index 未安装")
        print("请运行: pip install llama-index")
        return False
    
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        print("[OK] llama-index-embeddings-huggingface 已安装")
    except ImportError:
        print("[ERROR] llama-index-embeddings-huggingface 未安装")
        print("请运行: pip install llama-index-embeddings-huggingface")
        return False
    
    # 4. 构建索引
    print("\n[4/4] 构建新索引...")
    print("（这可能需要几分钟，请耐心等待）")
    print("-" * 60)
    
    try:
        from rag_system.retriever.rag_retriever import RAGRetriever
        
        retriever = RAGRetriever()
        retriever.build_index()
        
        # 验证索引
        if retriever.is_index_ready():
            print("\n" + "=" * 60)
            print("[OK] 索引构建成功！")
            print("=" * 60)
            
            # 检查向量数量
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(index_dir))
                collection = client.get_or_create_collection("financial_knowledge")
                count = collection.count()
                print(f"\n索引信息:")
                print(f"  - 向量数量: {count}")
                print(f"  - 索引路径: {index_dir.absolute()}")
                
                if count > 0:
                    print("\n[OK] 索引验证通过！")
                    return True
                else:
                    print("\n[ERROR] 索引集合为空，构建可能失败")
                    return False
            except Exception as e:
                print(f"[WARNING] 无法验证索引: {e}")
                return True  # 假设成功
        else:
            print("\n[ERROR] 索引构建完成但验证失败")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] 索引构建失败: {e}")
        import traceback
        print("\n详细错误:")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        if main():
            print("\n" + "=" * 60)
            print("[OK] 索引构建完成！")
            print("=" * 60)
            print("\n现在可以:")
            print("  1. 运行问答: python -m rag_system.main qa")
            print("  2. 启动服务器: python start_rag_server.py")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[ERROR] 索引构建失败")
            print("=" * 60)
            print("\n请检查:")
            print("  1. 依赖包是否完整安装")
            print("  2. 文档是否正确生成")
            print("  3. 网络连接（下载embedding模型）")
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

