"""
检查索引状态
"""

import sys
import io
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_index():
    """检查索引是否存在"""
    print("=" * 60)
    print("检查索引状态")
    print("=" * 60)
    
    # 检查ChromaDB目录
    chroma_db_path = Path("./data/vector_store/chroma_db")
    print(f"\n索引路径: {chroma_db_path.absolute()}")
    
    if not chroma_db_path.exists():
        print("[X] 索引目录不存在")
        print("\n请运行以下命令构建索引:")
        print("  python quick_start.py")
        return False
    
    print("[OK] 索引目录存在")
    
    # 检查ChromaDB集合
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(chroma_db_path))
        collection = client.get_or_create_collection("financial_knowledge")
        count = collection.count()
        
        print(f"[OK] ChromaDB集合存在")
        print(f"  集合名称: financial_knowledge")
        print(f"  向量数量: {count}")
        
        if count == 0:
            print("\n[WARNING] 集合为空，索引可能未正确构建")
            print("请重新运行: python quick_start.py")
            return False
        else:
            print("\n[OK] 索引状态正常")
            return True
            
    except ImportError:
        print("[WARNING] 无法检查ChromaDB（未安装chromadb）")
        return False
    except Exception as e:
        print(f"[ERROR] 检查索引时出错: {e}")
        return False

if __name__ == '__main__':
    if check_index():
        print("\n" + "=" * 60)
        print("索引已就绪，可以启动API服务器")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("索引未就绪，请先构建索引")
        print("=" * 60)

