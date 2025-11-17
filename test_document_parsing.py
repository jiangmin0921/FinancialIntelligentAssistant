"""
测试文档解析 - 检查文档是否能正确读取和解析
"""

import sys
import io
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_document_parsing():
    """测试文档解析"""
    print("=" * 60)
    print("测试文档解析")
    print("=" * 60)
    
    doc_dir = Path("./data/documents")
    if not doc_dir.exists():
        print("[ERROR] 文档目录不存在")
        return
    
    files = list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.docx"))
    print(f"\n找到 {len(files)} 个文档\n")
    
    try:
        from llama_index.core import SimpleDirectoryReader
        
        reader = SimpleDirectoryReader(
            input_dir=str(doc_dir),
            recursive=True
        )
        documents = reader.load_data()
        
        print(f"[OK] 成功读取 {len(documents)} 个文档对象\n")
        
        if len(documents) == 0:
            print("[ERROR] 文档读取为空！")
            return
        
        # 检查每个文档
        total_text_length = 0
        for i, doc in enumerate(documents, 1):
            text = doc.text if hasattr(doc, 'text') else str(doc)
            text_length = len(text)
            total_text_length += text_length
            
            print(f"文档 {i}:")
            print(f"  - 类型: {type(doc).__name__}")
            print(f"  - 文本长度: {text_length} 字符")
            print(f"  - 文本预览: {text[:100] if text_length > 0 else '(空)'}...")
            
            if hasattr(doc, 'metadata'):
                print(f"  - 元数据: {doc.metadata}")
            print()
        
        print(f"总文本长度: {total_text_length} 字符")
        
        if total_text_length == 0:
            print("\n[ERROR] 所有文档文本为空！")
            print("可能原因:")
            print("  1. PDF/Word文档格式问题")
            print("  2. 文档内容为空")
            print("  3. 文档解析器无法读取内容")
            return False
        else:
            print("\n[OK] 文档解析正常，可以构建索引")
            return True
            
    except Exception as e:
        print(f"[ERROR] 文档解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_document_parsing()

