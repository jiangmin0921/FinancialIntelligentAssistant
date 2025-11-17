"""
调试LLM初始化问题
"""

import sys
import os
import yaml
from pathlib import Path

# 修复Windows控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def debug_llm_init():
    """调试LLM初始化"""
    print("=" * 60)
    print("调试LLM初始化")
    print("=" * 60)
    
    # 1. 检查配置文件
    print("\n[1] 检查配置文件...")
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        llm_config = config['models']['llm']
        print(f"[OK] 配置文件读取成功")
        print(f"  Provider: {llm_config.get('provider')}")
        print(f"  Model: {llm_config.get('model_name')}")
        print(f"  API Key: {llm_config.get('api_key', '')[:10]}... (长度: {len(llm_config.get('api_key', ''))})")
        print(f"  API Base: {llm_config.get('api_base')}")
    except Exception as e:
        print(f"[ERROR] 配置文件读取失败: {e}")
        return
    
    # 2. 检查langchain包
    print("\n[2] 检查langchain包...")
    try:
        from langchain_openai import ChatOpenAI
        print("[OK] langchain_openai 已安装")
    except ImportError as e:
        print(f"[ERROR] langchain_openai 未安装: {e}")
        return
    
    try:
        from langchain_community.llms import Tongyi
        print("[OK] langchain_community.llms.Tongyi 可用")
        HAS_TONGYI = True
    except ImportError:
        print("[INFO] langchain_community.llms.Tongyi 不可用")
        HAS_TONGYI = False
    
    # 3. 测试环境变量设置
    print("\n[3] 测试环境变量设置...")
    api_key = llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
    api_base = llm_config.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    
    if not api_key:
        print("[ERROR] API密钥未设置")
        return
    
    print(f"[OK] API Key: {api_key[:10]}...")
    print(f"[OK] API Base: {api_base}")
    
    # 设置环境变量
    os.environ['OPENAI_API_KEY'] = api_key
    os.environ['OPENAI_API_BASE'] = api_base
    
    print(f"[OK] 环境变量已设置:")
    print(f"  OPENAI_API_KEY = {os.getenv('OPENAI_API_KEY')[:10]}...")
    print(f"  OPENAI_API_BASE = {os.getenv('OPENAI_API_BASE')}")
    
    # 4. 测试ChatOpenAI初始化
    print("\n[4] 测试ChatOpenAI初始化...")
    try:
        llm = ChatOpenAI(
            model=llm_config.get('model_name', 'qwen-turbo'),
            temperature=0.1
        )
        print("[OK] ChatOpenAI初始化成功")
        print(f"  Model: {llm.model_name if hasattr(llm, 'model_name') else 'N/A'}")
        print(f"  Base URL: {llm.openai_api_base if hasattr(llm, 'openai_api_base') else 'N/A'}")
    except Exception as e:
        print(f"[ERROR] ChatOpenAI初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 测试实际调用
    print("\n[5] 测试实际调用...")
    try:
        response = llm.invoke("你好")
        print(f"[OK] LLM调用成功")
        print(f"  响应类型: {type(response)}")
        if hasattr(response, 'content'):
            print(f"  响应内容: {response.content[:50]}...")
        else:
            print(f"  响应内容: {str(response)[:50]}...")
    except Exception as e:
        print(f"[ERROR] LLM调用失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. 测试SimpleRAGAgent初始化
    print("\n[6] 测试SimpleRAGAgent初始化...")
    try:
        from rag_system.agent.langchain_agent import SimpleRAGAgent
        print("[OK] SimpleRAGAgent导入成功")
        
        # 创建一个mock retriever（不需要真实索引）
        class MockRetriever:
            def retrieve(self, query):
                return {
                    'sources': [{
                        'text': '测试文档内容',
                        'metadata': {'file_name': 'test.pdf'}
                    }]
                }
        
        agent = SimpleRAGAgent(retriever=MockRetriever())
        print("[OK] SimpleRAGAgent初始化成功")
        
        # 测试查询
        print("\n[7] 测试查询...")
        result = agent.query("测试问题")
        print(f"[OK] 查询成功")
        print(f"  回答: {result.get('answer', '')[:100]}...")
        
    except Exception as e:
        print(f"[ERROR] SimpleRAGAgent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("[OK] 所有测试通过！")
    print("=" * 60)

if __name__ == '__main__':
    try:
        debug_llm_init()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

