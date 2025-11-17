"""
安装LangChain相关包
"""

import sys
import subprocess

def install_package(pkg):
    """安装包"""
    try:
        print(f"正在安装 {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        print(f"[OK] {pkg} 安装成功")
        return True
    except Exception as e:
        print(f"[ERROR] {pkg} 安装失败: {e}")
        return False

def main():
    print("=" * 60)
    print("安装LangChain相关包")
    print("=" * 60)
    
    packages = [
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-community>=0.0.20",
    ]
    
    print("\n将安装以下包:")
    for pkg in packages:
        print(f"  - {pkg}")
    
    choice = input("\n是否继续？(y/n): ").strip().lower()
    if choice != 'y':
        print("已取消")
        return
    
    print()
    success_count = 0
    for pkg in packages:
        if install_package(pkg):
            success_count += 1
        print()
    
    print("=" * 60)
    if success_count == len(packages):
        print("[OK] 所有包安装成功！")
        print("\n现在可以运行:")
        print("  python -m rag_system.main qa")
    else:
        print(f"[WARNING] {success_count}/{len(packages)} 个包安装成功")
        print("请检查错误信息并手动安装失败的包")
    print("=" * 60)

if __name__ == '__main__':
    main()

