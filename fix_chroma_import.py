"""
修复ChromaDB导入问题
"""

import sys
import subprocess

def check_and_install():
    """检查并安装ChromaDB向量存储支持"""
    print("=" * 60)
    print("修复ChromaDB导入问题")
    print("=" * 60)
    
    # 检查是否已安装
    print("\n[1] 检查ChromaVectorStore导入...")
    ChromaVectorStore = None
    
    try:
        from llama_index.vector_stores.chroma import ChromaVectorStore
        print("[OK] 从 llama_index.vector_stores.chroma 导入成功")
    except ImportError:
        try:
            from llama_index_vector_stores_chroma import ChromaVectorStore
            print("[OK] 从 llama_index_vector_stores_chroma 导入成功")
        except ImportError:
            print("[X] ChromaVectorStore 无法导入")
            print("\n[2] 正在安装 llama-index-vector-stores-chroma...")
            
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "llama-index-vector-stores-chroma"
                ])
                print("[OK] 安装成功")
                
                # 再次尝试导入
                try:
                    from llama_index.vector_stores.chroma import ChromaVectorStore
                    print("[OK] 导入成功")
                except ImportError:
                    from llama_index_vector_stores_chroma import ChromaVectorStore
                    print("[OK] 导入成功")
            except Exception as e:
                print(f"[ERROR] 安装失败: {e}")
                return False
    
    if ChromaVectorStore:
        print("\n[OK] ChromaVectorStore 可用")
        return True
    else:
        print("\n[ERROR] ChromaVectorStore 仍然不可用")
        return False

if __name__ == '__main__':
    if check_and_install():
        print("\n" + "=" * 60)
        print("[OK] 修复完成！")
        print("=" * 60)
        print("\n现在可以重新构建索引:")
        print("  python rebuild_index.py")
    else:
        print("\n" + "=" * 60)
        print("[ERROR] 修复失败")
        print("=" * 60)
        print("\n请手动安装:")
        print("  pip install llama-index-vector-stores-chroma")

