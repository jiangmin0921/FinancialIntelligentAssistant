"""
RAG检索器 - 封装LlamaIndex检索功能
支持混合检索（向量+关键词）和动态阈值调整
"""

from typing import List, Dict, Any, Optional
from rag_system.indexer.llama_indexer import LlamaIndexer
import re


class RAGRetriever:
    """RAG检索器 - 支持混合检索和动态阈值"""
    
    def __init__(self, indexer: Optional[LlamaIndexer] = None, use_hybrid: bool = True):
        """
        初始化检索器
        
        Args:
            indexer: LlamaIndex索引器
            use_hybrid: 是否使用混合检索（向量+关键词）
        """
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
        
        self.use_hybrid = use_hybrid
    
    def is_index_ready(self) -> bool:
        """检查索引是否已准备好"""
        return self.indexer is not None and self.indexer.index is not None
    
    def _keyword_search(self, query: str, all_sources: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        关键词检索（简单实现：基于文本匹配）
        
        Args:
            query: 查询文本
            all_sources: 所有文档源
            top_k: 返回top-k个结果
            
        Returns:
            按关键词匹配度排序的结果
        """
        # 提取关键词（简单分词）
        keywords = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', query)
        if not keywords:
            return []
        
        # 计算每个文档的关键词匹配分数
        scored_sources = []
        for source in all_sources:
            text = source.get('text', '').lower()
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # 计算关键词出现次数
                count = text.count(keyword_lower)
                score += count * (2 if len(keyword) > 1 else 1)  # 长词权重更高
            
            if score > 0:
                scored_sources.append({
                    **source,
                    'keyword_score': score
                })
        
        # 按关键词分数排序
        scored_sources.sort(key=lambda x: x.get('keyword_score', 0), reverse=True)
        return scored_sources[:top_k]
    
    def _adaptive_threshold(self, query: str, results: List[Dict]) -> float:
        """
        动态调整相似度阈值
        
        Args:
            query: 查询文本
            results: 检索结果
            
        Returns:
            调整后的阈值
        """
        base_threshold = 0.7
        
        # 根据查询长度调整
        if len(query) < 10:
            # 短查询提高阈值，要求更精确匹配
            threshold = 0.75
        elif len(query) > 50:
            # 长查询降低阈值，允许更多结果
            threshold = 0.65
        else:
            threshold = base_threshold
        
        # 根据结果数量调整
        if len(results) < 3:
            # 结果太少，降低阈值
            threshold = max(0.6, threshold - 0.05)
        elif len(results) > 10:
            # 结果太多，提高阈值
            threshold = min(0.8, threshold + 0.05)
        
        return threshold
    
    def _filter_by_threshold(self, results: List[Dict], threshold: float) -> List[Dict]:
        """根据阈值过滤结果"""
        filtered = []
        for result in results:
            score = result.get('score', 0)
            if score is not None and score >= threshold:
                filtered.append(result)
        return filtered
    
    def _rerank(self, vector_results: List[Dict], keyword_results: List[Dict], top_k: int) -> List[Dict]:
        """
        重排序：合并向量检索和关键词检索结果
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回top-k个结果
            
        Returns:
            重排序后的结果
        """
        # 创建结果映射（按文本内容去重）
        result_map = {}
        
        # 添加向量检索结果（权重0.6）
        for i, result in enumerate(vector_results):
            text = result.get('text', '')
            if text not in result_map:
                result_map[text] = {
                    **result,
                    'combined_score': (result.get('score', 0) or 0) * 0.6
                }
            else:
                # 合并分数
                result_map[text]['combined_score'] += (result.get('score', 0) or 0) * 0.6
        
        # 添加关键词检索结果（权重0.4）
        for result in keyword_results:
            text = result.get('text', '')
            keyword_score = result.get('keyword_score', 0)
            # 归一化关键词分数（假设最大为10）
            normalized_keyword_score = min(1.0, keyword_score / 10.0)
            
            if text not in result_map:
                result_map[text] = {
                    **result,
                    'combined_score': normalized_keyword_score * 0.4
                }
            else:
                # 合并分数
                result_map[text]['combined_score'] += normalized_keyword_score * 0.4
        
        # 按综合分数排序
        reranked = list(result_map.values())
        reranked.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return reranked[:top_k]
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        检索相关文档（支持混合检索）
        
        Args:
            query: 查询文本
            top_k: 返回top-k个结果
            
        Returns:
            检索结果
        """
        if not self.is_index_ready():
            raise ValueError("索引未初始化，请先构建索引。运行: python -m rag_system.main index")
        
        if top_k is None:
            top_k = 3
        
        # 向量检索（扩大检索范围，用于混合检索）
        vector_top_k = top_k * 2 if self.use_hybrid else top_k
        result = self.indexer.query(query, top_k=vector_top_k)
        vector_results = result.get('sources', [])
        
        if not self.use_hybrid:
            # 不使用混合检索，直接返回向量检索结果
            formatted_sources = []
            for source in vector_results[:top_k]:
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
        
        # 混合检索模式
        # 1. 关键词检索
        keyword_results = self._keyword_search(query, vector_results, top_k=top_k)
        
        # 2. 重排序
        reranked_results = self._rerank(vector_results, keyword_results, top_k=top_k * 2)
        
        # 3. 动态调整阈值
        threshold = self._adaptive_threshold(query, reranked_results)
        
        # 4. 根据阈值过滤
        filtered_results = self._filter_by_threshold(reranked_results, threshold)
        
        # 5. 如果过滤后结果太少，降低阈值
        if len(filtered_results) < top_k and len(reranked_results) > 0:
            threshold = max(0.5, threshold - 0.1)
            filtered_results = self._filter_by_threshold(reranked_results, threshold)
        
        # 6. 取top_k个结果
        final_results = filtered_results[:top_k] if filtered_results else reranked_results[:top_k]
        
        # 格式化返回结果
        formatted_sources = []
        for source in final_results:
            formatted_source = {
                'text': source.get('text', ''),
                'score': source.get('score') or source.get('combined_score'),
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

