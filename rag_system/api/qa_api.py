"""
RAG问答API接口
"""

from typing import Dict, Any
from rag_system.retriever.rag_retriever import RAGRetriever
from rag_system.agent.langchain_agent import SimpleRAGAgent


class QAService:
    """问答服务"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化问答服务"""
        self.retriever = RAGRetriever()
        if not self.retriever.is_index_ready():
            raise ValueError(
                "索引未初始化！\n"
                "请先运行以下命令构建索引：\n"
                "  python -m rag_system.main index\n"
                "或运行快速开始：\n"
                "  python quick_start.py"
            )
        self.agent = SimpleRAGAgent(config_path=config_path, retriever=self.retriever)
    
    def is_ready(self) -> bool:
        """检查服务是否已准备好"""
        return self.retriever.is_index_ready()
    
    def ask(self, question: str) -> Dict[str, Any]:
        """回答问题"""
        result = self.agent.query(question)
        
        # 格式化返回结果，包含引用来源
        sources_info = []
        for i, source in enumerate(result.get('sources', []), 1):
            doc_name = source.get('metadata', {}).get('file_name', '未知文档')
            # 提取段落信息（如果有）
            page_info = source.get('metadata', {}).get('page_label', '')
            if page_info:
                doc_name += f" (第{page_info}页)"
            
            sources_info.append({
                'index': i,
                'document': doc_name,
                'excerpt': source.get('text', '')[:150] + '...',  # 摘要
                'score': source.get('score')
            })
        
        return {
            'question': question,
            'answer': result.get('answer', ''),
            'sources': sources_info
        }


# 全局服务实例
_qa_service = None

def get_qa_service() -> QAService:
    """获取问答服务实例（单例模式）"""
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService()
    return _qa_service

