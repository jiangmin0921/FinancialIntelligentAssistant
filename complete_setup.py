"""
完整设置 - 安装依赖、构建索引、验证系统
"""

import sys
import io
import subprocess
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def install_package(pkg):
    """安装包"""
    try:
        print(f"  安装 {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def main():
    print("=" * 60)
    print("完整设置 RAG 系统")
    print("=" * 60)
    
    # 1. 检查并安装依赖
    print("\n[1/4] 检查依赖...")
    required_packages = [
        "llama-index",
        "llama-index-embeddings-huggingface",
        "llama-index-vector-stores-chroma",
        "chromadb",
        "sentence-transformers",
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            if pkg == "llama-index":
                __import__("llama_index")
            elif pkg == "llama-index-embeddings-huggingface":
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            elif pkg == "llama-index-vector-stores-chroma":
                from llama_index.vector_stores.chroma import ChromaVectorStore
            elif pkg == "chromadb":
                __import__("chromadb")
            elif pkg == "sentence-transformers":
                __import__("sentence_transformers")
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [X] {pkg} 未安装")
            missing.append(pkg)
    
    if missing:
        print(f"\n需要安装: {', '.join(missing)}")
        choice = input("是否自动安装？(y/n): ").strip().lower()
        if choice == 'y':
            for pkg in missing:
                if install_package(pkg):
                    print(f"  [OK] {pkg} 安装成功")
                else:
                    print(f"  [ERROR] {pkg} 安装失败")
        else:
            print("请手动安装: pip install " + " ".join(missing))
            return
    
    # 2. 检查文档
    print("\n[2/4] 检查文档...")
    doc_dir = Path("./data/documents")
    if not doc_dir.exists() or len(list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))) == 0:
        print("文档不存在，正在生成...")
        try:
            from rag_system.data_generator.generate_docs import DocumentGenerator
            generator = DocumentGenerator()
            files = generator.generate_financial_documents()
            
            import shutil
            doc_dir.mkdir(parents=True, exist_ok=True)
            for file in files:
                src = Path(file)
                dst = doc_dir / src.name
                if dst.exists():
                    dst.unlink()
                shutil.copy2(src, dst)
            print(f"  [OK] 已生成 {len(files)} 个文档")
        except Exception as e:
            print(f"  [ERROR] 文档生成失败: {e}")
            return
    else:
        files = list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))
        print(f"  [OK] 找到 {len(files)} 个文档")
    
    # 3. 删除旧索引
    print("\n[3/4] 清理旧索引...")
    index_dir = Path("./data/vector_store/chroma_db")
    if index_dir.exists():
        try:
            import shutil
            shutil.rmtree(index_dir)
            print("  [OK] 已删除旧索引")
        except Exception as e:
            print(f"  [WARNING] 无法删除: {e}")
    
    # 4. 构建索引
    print("\n[4/4] 构建索引...")
    print("（这可能需要几分钟，请耐心等待）")
    print("-" * 60)
    
    try:
        from rag_system.retriever.rag_retriever import RAGRetriever
        
        retriever = RAGRetriever()
        retriever.build_index()
        
        # 验证
        if retriever.is_index_ready():
            import chromadb
            client = chromadb.PersistentClient(path=str(index_dir))
            collection = client.get_or_create_collection("financial_knowledge")
            count = collection.count()
            
            if count > 0:
                print("\n" + "=" * 60)
                print("[OK] 索引构建成功！")
                print("=" * 60)
                print(f"向量数量: {count}")
                print("\n现在可以:")
                print("  1. 运行问答: python -m rag_system.main qa")
                print("  2. 启动服务器: python start_rag_server.py")
                return True
            else:
                print("\n[ERROR] 索引构建后向量数量为0")
                return False
        else:
            print("\n[ERROR] 索引构建失败")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] 构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

