"""
立即构建索引 - 解决索引未初始化问题
"""

import sys
import io
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    print("=" * 60)
    print("构建RAG索引")
    print("=" * 60)
    
    # 1. 检查文档
    print("\n[1/3] 检查文档...")
    doc_dir = Path("./data/documents")
    if not doc_dir.exists():
        print("[ERROR] 文档目录不存在")
        print("请先运行: python -m rag_system.main generate")
        return
    
    files = list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))
    if not files:
        print("[ERROR] 文档目录为空")
        print("请先运行: python -m rag_system.main generate")
        return
    
    print(f"[OK] 找到 {len(files)} 个文档:")
    for f in files:
        print(f"  - {f.name}")
    
    # 2. 删除旧索引（如果存在）
    print("\n[2/3] 清理旧索引...")
    index_dir = Path("./data/vector_store/chroma_db")
    if index_dir.exists():
        try:
            import shutil
            shutil.rmtree(index_dir)
            print("[OK] 已删除旧索引")
        except Exception as e:
            print(f"[WARNING] 无法删除旧索引: {e}")
            print("继续尝试构建新索引...")
    
    # 3. 构建索引
    print("\n[3/3] 构建新索引...")
    try:
        from rag_system.retriever.rag_retriever import RAGRetriever
        
        print("正在初始化检索器...")
        retriever = RAGRetriever()
        
        print("正在构建索引（这可能需要几分钟）...")
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
            except:
                pass
            
            print("\n现在可以启动API服务器:")
            print("  python start_rag_server.py")
        else:
            print("\n[ERROR] 索引构建完成但验证失败")
            print("请检查错误信息")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] 索引构建失败: {e}")
        import traceback
        print("\n详细错误:")
        traceback.print_exc()
        print("\n可能的原因:")
        print("  1. 依赖包未安装: pip install chromadb llama-index")
        print("  2. 网络问题（下载embedding模型）")
        print("  3. 文档格式问题")
        return False
    
    return True

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

