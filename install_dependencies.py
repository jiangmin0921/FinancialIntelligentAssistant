"""
安装依赖脚本 - 确保所有必要的包都已安装
"""

import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        print(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package} 安装失败: {e}")
        return False

def main():
    print("=" * 60)
    print("安装RAG系统依赖")
    print("=" * 60)
    print()
    
    # 核心依赖
    packages = [
        "llama-index>=0.10.0",
        "llama-index-embeddings-huggingface",
        "sentence-transformers>=2.2.0",
        "chromadb>=0.4.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-community>=0.0.20",
        "reportlab>=4.0.0",
        "python-docx>=1.1.0",
        "pypdf>=3.0.0",
        "pyyaml>=6.0",
        "flask>=2.3.0",
        "flask-cors>=4.0.0",
    ]
    
    print("将安装以下包:")
    for pkg in packages:
        print(f"  - {pkg}")
    print()
    
    choice = input("是否继续？(y/n): ").strip().lower()
    if choice != 'y':
        print("已取消")
        return
    
    print()
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"安装完成: {success_count}/{len(packages)} 个包安装成功")
    print("=" * 60)
    
    if success_count == len(packages):
        print("\n✓ 所有依赖已安装，可以运行 quick_start.py")
    else:
        print("\n⚠ 部分包安装失败，请检查错误信息")

if __name__ == '__main__':
    main()

