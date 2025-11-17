"""
RAG检索器 - 封装LlamaIndex检索功能
"""

from typing import List, Dict, Any, Optional
from rag_system.indexer.llama_indexer import LlamaIndexer


class RAGRetriever:
    """RAG检索器"""
    
    def __init__(self, indexer: Optional[LlamaIndexer] = None):
        """初始化检索器"""
        if indexer is None:
            self.indexer = LlamaIndexer()
            # 尝试加载已有索引
            try:
                self.indexer.load_index()
                print("[OK] 索引加载成功")
            except FileNotFoundError as e:
                # 这是正常的，首次运行索引不存在
                # 不打印错误，只设置index为None
                self.indexer.index = None
            except Exception as e:
                print(f"[WARNING] 加载索引时出错: {e}")
                self.indexer.index = None
        else:
            self.indexer = indexer
    
    def is_index_ready(self) -> bool:
        """检查索引是否已准备好"""
        return self.indexer is not None and self.indexer.index is not None
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """检索相关文档"""
        if not self.is_index_ready():
            raise ValueError("索引未初始化，请先构建索引。运行: python -m rag_system.main index")
        
        result = self.indexer.query(query, top_k=top_k)
        
        # 格式化返回结果
        formatted_sources = []
        for source in result.get('sources', []):
            formatted_source = {
                'text': source.get('text', ''),
                'score': source.get('score'),
                'metadata': source.get('metadata', {})
            }
            formatted_sources.append(formatted_source)
        
        return {
            'answer': result.get('answer', ''),
            'sources': formatted_sources
        }
    
    def build_index(self, documents_path: Optional[str] = None) -> None:
        """构建索引"""
        self.indexer.build_index(documents_path)
        # 构建完成后，索引已经保存在self.indexer.index中
        # 确保索引已准备好
        if self.indexer.index is None:
            raise RuntimeError("索引构建失败，index为None")
        print("[OK] 索引构建并保存成功")

