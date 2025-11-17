"""
启动RAG API服务器
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """启动Flask API服务器"""
    print("=" * 60)
    print("财务助手 RAG API 服务器")
    print("=" * 60)
    
    # 检查索引是否存在且有效
    index_path = Path("./data/vector_store/chroma_db")
    index_valid = False
    
    if index_path.exists():
        # 尝试检查索引是否有效
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(index_path))
            collection = client.get_or_create_collection("financial_knowledge")
            count = collection.count()
            if count > 0:
                index_valid = True
                print(f"\n[OK] 索引已存在（包含 {count} 个向量）")
        except:
            pass
    
    if not index_valid:
        print("\n" + "=" * 60)
        print("⚠ 警告: 索引不存在或无效！")
        print("=" * 60)
        print("\n请先运行以下命令构建索引：")
        print("  方式1（推荐）: python fix_and_build_index.py")
        print("  方式2: python quick_start.py")
        print("  方式3: python -m rag_system.main index")
        print("\n是否继续启动服务器？（索引不存在时将无法回答问题）")
        choice = input("(y/n): ").strip().lower()
        if choice != 'y':
            print("已取消启动")
            return
    
    print("\n正在启动API服务器...")
    print("API地址: http://localhost:5000")
    print("健康检查: http://localhost:5000/api/health")
    print("问答接口: http://localhost:5000/api/qa")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 启动Flask服务器
    from rag_system.api.flask_api import app, init_qa_service
    
    if init_qa_service():
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("\n❌ RAG服务初始化失败！")
        print("请检查:")
        print("  1. 索引是否已构建")
        print("  2. API密钥是否正确配置")
        print("  3. 依赖包是否已安装")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")

