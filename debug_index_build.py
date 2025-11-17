"""
调试索引构建过程
"""

import sys
import io
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def debug_build():
    """调试索引构建"""
    print("=" * 60)
    print("调试索引构建过程")
    print("=" * 60)
    
    # 1. 检查文档
    print("\n[1] 检查文档...")
    doc_dir = Path("./data/documents")
    if not doc_dir.exists():
        print("[ERROR] 文档目录不存在")
        return
    
    files = list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))
    print(f"[OK] 找到 {len(files)} 个文档:")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
    
    # 2. 测试文档读取
    print("\n[2] 测试文档读取...")
    try:
        from llama_index.core import SimpleDirectoryReader
        
        reader = SimpleDirectoryReader(
            input_dir=str(doc_dir),
            recursive=True
        )
        documents = reader.load_data()
        print(f"[OK] 成功读取 {len(documents)} 个文档对象")
        
        if len(documents) == 0:
            print("[ERROR] 文档读取为空！")
            return
        
        # 显示第一个文档的信息
        if documents:
            doc = documents[0]
            print(f"  第一个文档:")
            print(f"    - 类型: {type(doc)}")
            print(f"    - 文本长度: {len(doc.text) if hasattr(doc, 'text') else 'N/A'}")
            print(f"    - 文本预览: {doc.text[:100] if hasattr(doc, 'text') else 'N/A'}...")
    except Exception as e:
        print(f"[ERROR] 文档读取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 测试embedding模型
    print("\n[3] 测试embedding模型...")
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        
        embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5"
        )
        print("[OK] Embedding模型加载成功")
        
        # 测试embedding
        test_text = "测试文本"
        embedding = embed_model.get_query_embedding(test_text)
        print(f"[OK] Embedding测试成功，向量维度: {len(embedding)}")
    except Exception as e:
        print(f"[ERROR] Embedding模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 测试节点解析器
    print("\n[4] 测试节点解析器...")
    try:
        from llama_index.core.node_parser import SentenceSplitter
        
        node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        print("[OK] 节点解析器创建成功")
        
        # 测试切分
        if documents:
            nodes = node_parser.get_nodes_from_documents([documents[0]])
            print(f"[OK] 节点切分测试成功，生成 {len(nodes)} 个节点")
            if nodes:
                print(f"  第一个节点长度: {len(nodes[0].text)}")
    except Exception as e:
        print(f"[ERROR] 节点解析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 测试ChromaDB
    print("\n[5] 测试ChromaDB...")
    try:
        import chromadb
        
        # 尝试多种导入方式
        ChromaVectorStore = None
        try:
            from llama_index.vector_stores.chroma import ChromaVectorStore
        except ImportError:
            try:
                from llama_index_vector_stores_chroma import ChromaVectorStore
            except ImportError:
                try:
                    from llama_index.core.vector_stores import ChromaVectorStore
                except ImportError:
                    print("[ERROR] 无法导入ChromaVectorStore")
                    print("请安装: pip install llama-index-vector-stores-chroma")
                    return
        
        from llama_index.core import StorageContext
        
        # 创建临时测试集合
        test_dir = Path("./data/vector_store/test_chroma")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        
        chroma_client = chromadb.PersistentClient(path=str(test_dir))
        chroma_collection = chroma_client.create_collection("test_collection")
        
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        print("[OK] ChromaDB连接成功")
        
        # 清理测试
        shutil.rmtree(test_dir)
    except Exception as e:
        print(f"[ERROR] ChromaDB测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. 完整构建测试
    print("\n[6] 完整构建测试...")
    try:
        from llama_index.core import VectorStoreIndex, Settings, StorageContext
        import chromadb
        
        # 导入ChromaVectorStore（使用之前测试的导入方式）
        if ChromaVectorStore is None:
            print("[ERROR] ChromaVectorStore未导入")
            return
        
        # 设置embedding模型
        Settings.embed_model = embed_model
        
        # 创建ChromaDB
        index_dir = Path("./data/vector_store/debug_chroma")
        if index_dir.exists():
            import shutil
            shutil.rmtree(index_dir)
        
        chroma_client = chromadb.PersistentClient(path=str(index_dir))
        chroma_collection = chroma_client.get_or_create_collection("test_knowledge")
        
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        print("正在构建索引（使用第一个文档测试）...")
        index = VectorStoreIndex.from_documents(
            [documents[0]],  # 只使用第一个文档测试
            storage_context=storage_context,
            node_parser=node_parser,
            show_progress=True
        )
        
        # 检查向量数量
        count = chroma_collection.count()
        print(f"[OK] 索引构建完成，向量数量: {count}")
        
        if count > 0:
            print("[OK] 索引构建测试成功！")
        else:
            print("[ERROR] 索引构建后向量数量为0")
            print("可能的原因:")
            print("  1. 文档内容为空")
            print("  2. 节点切分失败")
            print("  3. 向量化失败")
            print("  4. 保存到ChromaDB失败")
        
        # 清理测试
        shutil.rmtree(index_dir)
        
    except Exception as e:
        print(f"[ERROR] 完整构建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)

if __name__ == '__main__':
    debug_build()

