"""
修复并构建索引 - 自动检查和修复索引问题
"""

import sys
import io
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_dependencies():
    """检查依赖"""
    print("=" * 60)
    print("检查依赖包")
    print("=" * 60)
    
    missing = []
    
    # 检查关键包
    packages = {
        'chromadb': 'chromadb',
        'llama_index': 'llama-index',
        'sentence_transformers': 'sentence-transformers',
        'yaml': 'pyyaml'
    }
    
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"[OK] {package} 已安装")
        except ImportError:
            print(f"[X] {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n缺少以下包: {', '.join(missing)}")
        print("正在安装...")
        import subprocess
        for pkg in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                print(f"[OK] {pkg} 安装成功")
            except Exception as e:
                print(f"[ERROR] {pkg} 安装失败: {e}")
        return False
    else:
        print("\n[OK] 所有依赖已安装")
        return True

def check_documents():
    """检查文档"""
    print("\n" + "=" * 60)
    print("检查文档")
    print("=" * 60)
    
    doc_dir = Path("./data/documents")
    if not doc_dir.exists():
        print("[X] 文档目录不存在")
        return False
    
    files = list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))
    if not files:
        print("[X] 文档目录为空")
        print("需要先生成文档")
        return False
    
    print(f"[OK] 找到 {len(files)} 个文档:")
    for f in files:
        print(f"  - {f.name}")
    
    return True

def rebuild_index():
    """重新构建索引"""
    print("\n" + "=" * 60)
    print("构建索引")
    print("=" * 60)
    
    # 删除旧索引（如果存在）
    index_dir = Path("./data/vector_store/chroma_db")
    if index_dir.exists():
        print("删除旧索引...")
        import shutil
        try:
            shutil.rmtree(index_dir)
            print("[OK] 旧索引已删除")
        except Exception as e:
            print(f"[WARNING] 无法删除旧索引: {e}")
    
    # 构建新索引
    try:
        from rag_system.retriever.rag_retriever import RAGRetriever
        retriever = RAGRetriever()
        retriever.build_index()
        
        if retriever.is_index_ready():
            print("\n[OK] 索引构建成功！")
            return True
        else:
            print("\n[X] 索引构建失败")
            return False
    except Exception as e:
        print(f"\n[X] 索引构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("修复并构建索引")
    print("=" * 60)
    
    # 1. 检查依赖
    if not check_dependencies():
        print("\n请先安装缺失的依赖包")
        return
    
    # 2. 检查文档
    if not check_documents():
        print("\n正在生成文档...")
        try:
            from rag_system.data_generator.generate_docs import DocumentGenerator
            generator = DocumentGenerator()
            files = generator.generate_financial_documents()
            
            # 复制到documents目录
            import shutil
            doc_dir = Path("./data/documents")
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                src = Path(file)
                dst = doc_dir / src.name
                if dst.exists():
                    dst.unlink()
                shutil.copy2(src, dst)
            
            print(f"[OK] 已生成 {len(files)} 个文档")
        except Exception as e:
            print(f"[ERROR] 文档生成失败: {e}")
            return
    
    # 3. 构建索引
    if rebuild_index():
        print("\n" + "=" * 60)
        print("[OK] 索引构建完成！")
        print("=" * 60)
        print("\n现在可以启动API服务器:")
        print("  python start_rag_server.py")
    else:
        print("\n" + "=" * 60)
        print("[ERROR] 索引构建失败")
        print("=" * 60)
        print("\n请检查:")
        print("  1. 网络连接（下载embedding模型需要网络）")
        print("  2. 文档是否正确生成")
        print("  3. 依赖包是否完整安装")

if __name__ == '__main__':
    main()

