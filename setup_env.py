"""
环境设置脚本 - 帮助用户快速配置环境
"""

import os
import sys
from pathlib import Path

def create_directories():
    """创建必要的目录"""
    dirs = [
        "./data/documents",
        "./data/generated",
        "./data/vector_store"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {dir_path}")

def check_config():
    """检查配置文件"""
    config_file = Path("config.yaml")
    if not config_file.exists():
        print("✗ config.yaml 不存在")
        return False
    print("✓ config.yaml 存在")
    return True

def check_api_keys():
    """检查API密钥"""
    openai_key = os.getenv('OPENAI_API_KEY')
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    
    if not openai_key and not dashscope_key:
        print("⚠ 警告: 未设置API密钥")
        print("  请设置环境变量:")
        print("    export OPENAI_API_KEY='your-key'")
        print("    或")
        print("    export DASHSCOPE_API_KEY='your-key'")
        return False
    
    if openai_key:
        print("✓ OPENAI_API_KEY 已设置")
    if dashscope_key:
        print("✓ DASHSCOPE_API_KEY 已设置")
    
    return True

def main():
    print("=" * 50)
    print("RAG系统环境设置")
    print("=" * 50)
    
    print("\n1. 创建目录...")
    create_directories()
    
    print("\n2. 检查配置文件...")
    check_config()
    
    print("\n3. 检查API密钥...")
    check_api_keys()
    
    print("\n" + "=" * 50)
    print("环境设置完成！")
    print("\n下一步:")
    print("  1. 生成文档: python -m rag_system.main generate")
    print("  2. 构建索引: python -m rag_system.main index")
    print("  3. 开始问答: python -m rag_system.main qa")
    print("=" * 50)

if __name__ == "__main__":
    main()

