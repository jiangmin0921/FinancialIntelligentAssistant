"""
RAG系统主程序
"""

import argparse
import sys
from pathlib import Path

from rag_system.data_generator.generate_docs import DocumentGenerator
from rag_system.retriever.rag_retriever import RAGRetriever
from rag_system.api.qa_api import QAService


def generate_documents():
    """生成文档"""
    print("=" * 50)
    print("开始生成财务文档...")
    print("=" * 50)
    
    generator = DocumentGenerator()
    files = generator.generate_financial_documents()
    
    print(f"\n成功生成 {len(files)} 个文档：")
    for file in files:
        print(f"  ✓ {file}")
    
    # 将生成的文档复制到documents目录
    import shutil
    from pathlib import Path
    
    documents_dir = Path("./data/documents")
    documents_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        src = Path(file)
        dst = documents_dir / src.name
        shutil.copy2(src, dst)
        print(f"  已复制到: {dst}")
    
    print("\n文档生成完成！")


def build_index():
    """构建索引"""
    print("=" * 50)
    print("开始构建索引...")
    print("=" * 50)
    
    retriever = RAGRetriever()
    retriever.build_index()
    
    print("\n索引构建完成！")


def interactive_qa():
    """交互式问答"""
    print("=" * 50)
    print("财务助手问答系统")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 50)
    
    qa_service = QAService()
    
    while True:
        try:
            question = input("\n请输入您的问题: ").strip()
            
            if question.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            
            if not question:
                continue
            
            print("\n正在思考...")
            result = qa_service.ask(question)
            
            print("\n" + "=" * 50)
            print("回答：")
            print("-" * 50)
            print(result['answer'])
            
            if result['sources']:
                print("\n" + "-" * 50)
                print("引用来源：")
                for source in result['sources']:
                    print(f"  [{source['index']}] {source['document']}")
                    if source.get('excerpt'):
                        print(f"      {source['excerpt']}")
            
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='财务助手RAG系统')
    parser.add_argument(
        'command',
        choices=['generate', 'index', 'qa'],
        help='命令: generate-生成文档, index-构建索引, qa-问答'
    )
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_documents()
    elif args.command == 'index':
        build_index()
    elif args.command == 'qa':
        interactive_qa()


if __name__ == "__main__":
    main()

