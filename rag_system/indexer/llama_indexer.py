"""
使用LlamaIndex进行文档索引和检索
"""

import os
from pathlib import Path
from typing import List, Optional
import yaml

try:
    # 尝试新版本导入
    try:
        from llama_index.core import (
            VectorStoreIndex,
            SimpleDirectoryReader,
            StorageContext,
            load_index_from_storage,
            Settings,
        )
        from llama_index.core.node_parser import (
            SemanticSplitterNodeParser,
            SentenceSplitter,
        )
        HAS_LLAMAINDEX = True
    except ImportError:
        # 尝试旧版本导入
        try:
            from llama_index import (
                VectorStoreIndex,
                SimpleDirectoryReader,
                StorageContext,
                load_index_from_storage,
                ServiceContext,
            )
            from llama_index.node_parser import (
                SemanticSplitterNodeParser,
                SentenceSplitter,
            )
            HAS_LLAMAINDEX = True
        except ImportError:
            HAS_LLAMAINDEX = False
            VectorStoreIndex = None
            SimpleDirectoryReader = None
            StorageContext = None
            load_index_from_storage = None
            Settings = None
            SemanticSplitterNodeParser = None
            SentenceSplitter = None
    
    # Embedding模型导入
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
    except ImportError:
        try:
            from llama_index.embeddings import OpenAIEmbedding
        except ImportError:
            OpenAIEmbedding = None
    
    # HuggingFace Embedding导入
    HuggingFaceEmbedding = None
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError:
        try:
            from llama_index.embeddings.huggingface.base import HuggingFaceEmbedding
        except ImportError:
            try:
                # 尝试从llama-index-embeddings-huggingface导入
                from llama_index_embeddings_huggingface import HuggingFaceEmbedding
            except ImportError:
                HuggingFaceEmbedding = None
    
    # ChromaDB导入
    ChromaVectorStore = None
    try:
        # 尝试新版本导入（llama-index-vector-stores-chroma）
        try:
            from llama_index.vector_stores.chroma import ChromaVectorStore
        except ImportError:
            try:
                # 尝试从llama-index-vector-stores-chroma直接导入
                from llama_index_vector_stores_chroma import ChromaVectorStore
            except ImportError:
                try:
                    # 尝试从core.vector_stores导入
                    from llama_index.core.vector_stores import ChromaVectorStore
                except ImportError:
                    try:
                        # 尝试旧版本导入
                        from llama_index.vector_stores import ChromaVectorStore
                    except ImportError:
                        ChromaVectorStore = None
    except Exception:
        ChromaVectorStore = None
    
    import chromadb
    HAS_LLAMAINDEX = True
except ImportError as e:
    HAS_LLAMAINDEX = False
    print(f"警告: llama-index相关包未安装: {e}")


class LlamaIndexer:
    """LlamaIndex索引器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化索引器"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.documents_dir = Path(self.config['data']['documents_dir'])
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        self.vector_store_dir = Path(self.config['vector_store']['persist_dir'])
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_strategy = self.config['document']['chunk_strategy']
        self.chunk_size = self.config['document']['chunk_size']
        self.chunk_overlap = self.config['document']['chunk_overlap']
        
        # 初始化embedding模型
        self._setup_embedding()
        
        # 初始化节点解析器
        self._setup_node_parser()
        
        # 初始化索引
        self.index = None
        
    def _setup_embedding(self):
        """设置embedding模型"""
        embedding_config = self.config['models']['embedding']
        provider = embedding_config.get('provider', 'local')
        
        if provider == 'openai' and OpenAIEmbedding:
            # 使用OpenAI兼容的embedding模型
            try:
                print("正在初始化OpenAI embedding模型...")
                self.embed_model = OpenAIEmbedding(
                    model=embedding_config.get('model_name', 'text-embedding-3-small'),
                    api_key=embedding_config.get('api_key') or os.getenv('OPENAI_API_KEY'),
                    timeout=60.0  # 设置超时时间
                )
                print("✓ OpenAI embedding模型初始化成功")
            except Exception as e:
                print(f"⚠ OpenAI embedding初始化失败: {e}")
                print("正在切换到本地embedding模型...")
                self._setup_local_embedding()
        else:
            # 使用本地模型（默认）
            print("正在初始化本地embedding模型（首次运行需要下载模型，请耐心等待）...")
            self._setup_local_embedding()
        
        # 设置全局embedding模型
        try:
            Settings.embed_model = self.embed_model
        except:
            # 如果Settings不存在，使用ServiceContext（旧版本）
            pass
    
    def _setup_local_embedding(self):
        """设置本地embedding模型"""
        embedding_config = self.config['models']['embedding']
        model_name = embedding_config.get('model_name', 'BAAI/bge-small-zh-v1.5')
        
        # 尝试多种导入方式
        HuggingFaceEmbeddingClass = None
        
        # 方式1: 从llama_index.embeddings.huggingface导入
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding as HFEmbedding
            HuggingFaceEmbeddingClass = HFEmbedding
        except ImportError:
            # 方式2: 从llama-index-embeddings-huggingface导入
            try:
                from llama_index_embeddings_huggingface import HuggingFaceEmbedding as HFEmbedding
                HuggingFaceEmbeddingClass = HFEmbedding
            except ImportError:
                # 方式3: 尝试其他可能的路径
                try:
                    from llama_index.embeddings.huggingface.base import HuggingFaceEmbedding as HFEmbedding
                    HuggingFaceEmbeddingClass = HFEmbedding
                except ImportError:
                    pass
        
        if HuggingFaceEmbeddingClass is None:
            print("❌ 无法导入HuggingFaceEmbedding")
            print("请安装: pip install llama-index-embeddings-huggingface")
            print("或者: pip install sentence-transformers")
            self.embed_model = None
            return
        
        try:
            print(f"正在加载本地embedding模型: {model_name}")
            print("（首次运行需要下载模型，请耐心等待...）")
            
            # 检查是否设置了镜像源
            import os
            hf_endpoint = os.getenv('HF_ENDPOINT', '')
            if hf_endpoint:
                print(f"使用镜像源: {hf_endpoint}")
            else:
                print("提示: 如果下载超时，可以设置镜像源:")
                print("  Windows: set HF_ENDPOINT=https://hf-mirror.com")
                print("  Linux/Mac: export HF_ENDPOINT=https://hf-mirror.com")
            
            # 创建embedding模型
            try:
                # 尝试直接加载
                self.embed_model = HuggingFaceEmbeddingClass(
                    model_name=model_name,
                    trust_remote_code=True
                )
            except (Exception, TimeoutError, ConnectionError) as e1:
                error_msg = str(e1).lower()
                if 'timeout' in error_msg or 'connection' in error_msg:
                    # 网络超时，尝试使用镜像
                    print(f"\n⚠ 下载超时，正在尝试使用镜像源...")
                    if not hf_endpoint:
                        # 自动设置镜像
                        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                        print("已自动设置镜像源: https://hf-mirror.com")
                    
                    try:
                        # 重新创建（会使用新的镜像设置）
                        self.embed_model = HuggingFaceEmbeddingClass(
                            model_name=model_name,
                            trust_remote_code=True
                        )
                    except Exception as e2:
                        print(f"\n❌ 镜像下载也失败: {e2}")
                        print("\n建议:")
                        print("  1. 检查网络连接")
                        print("  2. 手动设置镜像源后重试:")
                        print("     set HF_ENDPOINT=https://hf-mirror.com")
                        print("  3. 或手动下载模型:")
                        print("     huggingface-cli download BAAI/bge-small-zh-v1.5")
                        raise e2
                else:
                    raise e1
            
            print("✓ 本地embedding模型加载成功")
        except Exception as e:
            print(f"❌ 无法加载embedding模型: {e}")
            print("请确保已安装:")
            print("  pip install llama-index-embeddings-huggingface")
            print("  pip install sentence-transformers")
            self.embed_model = None
    
    def _setup_node_parser(self):
        """设置节点解析器（chunk策略）"""
        if not HAS_LLAMAINDEX or SentenceSplitter is None:
            raise ImportError(
                "llama-index未安装！\n"
                "请运行: pip install llama-index llama-index-embeddings-huggingface"
            )
        
        if self.chunk_strategy == "semantic":
            # 按语义切分（需要embedding模型）
            if self.embed_model is None:
                print("⚠ 警告: embedding模型未加载，语义切分不可用，切换到按页切分")
                self.chunk_strategy = "page"
                self.node_parser = SentenceSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
            else:
                try:
                    if SemanticSplitterNodeParser is None:
                        raise ImportError("SemanticSplitterNodeParser不可用")
                    self.node_parser = SemanticSplitterNodeParser(
                        buffer_size=1,
                        breakpoint_percentile_threshold=95,
                        embed_model=self.embed_model
                    )
                except Exception as e:
                    print(f"⚠ 语义切分初始化失败: {e}，切换到按页切分")
                    self.node_parser = SentenceSplitter(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap
                    )
        elif self.chunk_strategy == "page":
            # 按页切分
            self.node_parser = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:  # title or default
            # 按标题切分（使用句子分割器作为默认）
            self.node_parser = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
    
    def build_index(self, documents_path: Optional[str] = None) -> None:
        """构建索引"""
        if not HAS_LLAMAINDEX:
            raise ImportError("需要安装llama-index相关包")
        
        # 确定文档路径
        if documents_path:
            doc_path = Path(documents_path)
        else:
            doc_path = self.documents_dir
        
        if not doc_path.exists():
            raise FileNotFoundError(f"文档目录不存在: {doc_path}")
        
        print(f"正在从 {doc_path} 读取文档...")
        
        # 读取文档
        reader = SimpleDirectoryReader(
            input_dir=str(doc_path),
            recursive=True
        )
        documents = reader.load_data()
        
        print(f"已加载 {len(documents)} 个文档")
        
        # 确保embedding模型已设置
        if self.embed_model is None:
            raise RuntimeError("Embedding模型未初始化，无法构建索引")
        
        # 设置全局embedding模型
        try:
            Settings.embed_model = self.embed_model
        except:
            pass
        
        # 初始化ChromaDB
        chroma_db_path = self.vector_store_dir / "chroma_db"
        chroma_client = chromadb.PersistentClient(
            path=str(chroma_db_path)
        )
        
        # 如果集合已存在且为空，先删除
        try:
            existing_collection = chroma_client.get_collection("financial_knowledge")
            if existing_collection.count() == 0:
                chroma_client.delete_collection("financial_knowledge")
                print("已删除空的旧集合")
        except:
            pass
        
        chroma_collection = chroma_client.get_or_create_collection("financial_knowledge")
        
        if ChromaVectorStore:
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # 构建索引
            print("正在构建索引...")
            print(f"  文档数量: {len(documents)}")
            print(f"  使用embedding模型: {type(self.embed_model).__name__}")
            print(f"  节点解析器: {type(self.node_parser).__name__}")
            
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                node_parser=self.node_parser,
                embed_model=self.embed_model,  # 显式传入embedding模型
                show_progress=True
            )
            
            # 等待向量保存完成
            import time
            time.sleep(1)  # 给ChromaDB一点时间保存
            
            # 验证向量数量
            final_count = chroma_collection.count()
            print(f"索引构建完成！向量数量: {final_count}")
            
            if final_count == 0:
                print("[WARNING] 向量数量为0，可能存在问题")
                print("检查:")
                print("  1. 文档是否有内容")
                print("  2. 节点切分是否成功")
                print("  3. Embedding模型是否正常工作")
        else:
            # 如果ChromaVectorStore不可用，使用默认向量存储
            print("正在构建索引（使用默认向量存储）...")
            self.index = VectorStoreIndex.from_documents(
                documents,
                node_parser=self.node_parser,
                show_progress=True
            )
        
        # 确保索引已保存（ChromaDB会自动持久化）
        if self.index is None:
            raise RuntimeError("索引构建失败，index为None")
        
        # 最终验证
        if ChromaVectorStore:
            final_count = chroma_collection.count()
            if final_count == 0:
                raise RuntimeError(
                    f"索引构建完成但向量数量为0。\n"
                    f"可能原因：\n"
                    f"  1. 文档内容为空或无法解析\n"
                    f"  2. 节点切分失败\n"
                    f"  3. Embedding模型未正确工作\n"
                    f"请检查文档内容和依赖包。"
                )
    
    def load_index(self) -> None:
        """加载已有索引"""
        if not HAS_LLAMAINDEX:
            raise ImportError("需要安装llama-index相关包")
        
        chroma_db_path = self.vector_store_dir / "chroma_db"
        if not chroma_db_path.exists():
            raise FileNotFoundError(f"索引不存在，请先构建索引。路径: {chroma_db_path}")
        
        try:
            if ChromaVectorStore:
                # 使用ChromaDB时，直接从vector_store加载
                chroma_client = chromadb.PersistentClient(path=str(chroma_db_path))
                chroma_collection = chroma_client.get_or_create_collection("financial_knowledge")
                
                # 检查集合是否有数据
                count = chroma_collection.count()
                if count == 0:
                    raise FileNotFoundError("索引集合为空，请重新构建索引")
                
                # 创建vector_store
                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                
                # 确保embedding模型已设置
                if self.embed_model is None:
                    self._setup_embedding()
                
                if self.embed_model is None:
                    raise RuntimeError("Embedding模型未初始化，无法加载索引")
                
                # 设置全局embedding模型
                try:
                    Settings.embed_model = self.embed_model
                except:
                    pass
                
                # 直接从vector_store创建索引（不使用load_index_from_storage）
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                self.index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context,
                    embed_model=self.embed_model
                )
                
                if self.index is None:
                    raise RuntimeError("从vector_store创建索引失败，返回None")
                
                print(f"索引加载完成！(包含 {count} 个向量)")
            else:
                # 尝试从默认存储加载
                storage_context = StorageContext.from_defaults(
                    persist_dir=str(self.vector_store_dir)
                )
                self.index = load_index_from_storage(storage_context)
                if self.index is None:
                    raise RuntimeError("从存储加载索引失败，返回None")
                print("索引加载完成！")
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "索引不存在" in error_msg or "FileNotFoundError" in str(type(e)):
                raise FileNotFoundError(f"索引不存在，请先构建索引。路径: {chroma_db_path}")
            else:
                raise RuntimeError(f"无法加载索引: {error_msg}。请重新构建索引。")
    
    def query(self, question: str, top_k: Optional[int] = None) -> List:
        """查询索引（仅返回检索结果，不触发LLM生成）"""
        if self.index is None:
            raise ValueError("索引未初始化，请先构建或加载索引")
        
        if top_k is None:
            top_k = self.config['rag']['top_k']
        
        # 直接使用retriever获取节点，避免LlamaIndex内部再调用默认LLM
        retriever = self.index.as_retriever(similarity_top_k=top_k)
        retrieved_nodes = retriever.retrieve(question)
        
        source_nodes = []
        for node in retrieved_nodes:
            source_nodes.append({
                'text': getattr(node, 'text', ''),
                'score': getattr(node, 'score', None),
                'metadata': getattr(node, 'metadata', {}) or {}
            })
        
        # 不返回answer，由上层LLM（如通义千问）负责生成
        return {
            'answer': '',
            'sources': source_nodes
        }


if __name__ == "__main__":
    # 测试索引器
    indexer = LlamaIndexer()
    
    # 构建索引
    indexer.build_index()
    
    # 测试查询
    result = indexer.query("差旅费报销的标准是什么？")
    print("\n回答：")
    print(result['answer'])
    print("\n来源：")
    for i, source in enumerate(result['sources'], 1):
        print(f"{i}. {source.get('metadata', {}).get('file_name', '未知')}")
        print(f"   相似度: {source.get('score', 'N/A')}")
        print(f"   内容: {source['text'][:100]}...")

