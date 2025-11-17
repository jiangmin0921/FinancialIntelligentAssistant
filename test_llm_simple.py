"""
简单测试LLM初始化
"""

import os
import yaml

# 读取配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

llm_config = config['models']['llm']
api_key = llm_config.get('api_key')
api_base = llm_config.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

print(f"API Key: {api_key[:10]}...")
print(f"API Base: {api_base}")

# 设置环境变量
os.environ['OPENAI_API_KEY'] = api_key
os.environ['OPENAI_API_BASE'] = api_base

print(f"\n环境变量:")
print(f"  OPENAI_API_KEY = {os.getenv('OPENAI_API_KEY')[:10]}...")
print(f"  OPENAI_API_BASE = {os.getenv('OPENAI_API_BASE')}")

# 测试初始化
print("\n初始化ChatOpenAI...")
from langchain_openai import ChatOpenAI

try:
    llm = ChatOpenAI(
        model=llm_config.get('model_name', 'qwen-turbo'),
        temperature=0.1
    )
    print("[OK] 初始化成功")
    
    # 检查属性
    print(f"\nLLM属性:")
    print(f"  model: {llm.model_name if hasattr(llm, 'model_name') else 'N/A'}")
    if hasattr(llm, 'openai_api_key'):
        key = str(llm.openai_api_key) if llm.openai_api_key else 'None'
        print(f"  openai_api_key: {key[:10] if key != 'None' else 'None'}...")
    if hasattr(llm, 'openai_api_base'):
        print(f"  openai_api_base: {llm.openai_api_base}")
    
    # 测试调用
    print("\n测试调用...")
    response = llm.invoke("你好")
    print(f"[OK] 调用成功")
    print(f"  响应: {response.content if hasattr(response, 'content') else response}")
    
except Exception as e:
    print(f"[ERROR] 失败: {e}")
    import traceback
    traceback.print_exc()

