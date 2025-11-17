"""
一键安装依赖并构建索引
"""

import sys
import subprocess
import io

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def install_package(package):
    """安装包"""
    try:
        print(f"正在安装 {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[OK] {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {package} 安装失败")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print("=" * 60)
    print("一键安装依赖并构建索引")
    print("=" * 60)
    
    # 必需的包
    required_packages = [
        "llama-index>=0.10.0",
        "llama-index-embeddings-huggingface",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
    ]
    
    print("\n[步骤1] 安装依赖包...")
    print("=" * 60)
    
    failed = []
    for pkg in required_packages:
        if not install_package(pkg):
            failed.append(pkg)
        print()
    
    if failed:
        print(f"[ERROR] 以下包安装失败: {', '.join(failed)}")
        print("请手动安装: pip install " + " ".join(failed))
        return False
    
    print("[OK] 所有依赖包已安装")
    
    # 构建索引
    print("\n[步骤2] 构建索引...")
    print("=" * 60)
    
    try:
        from build_index_now import main as build_main
        return build_main()
    except ImportError:
        print("[ERROR] 无法导入构建脚本")
        print("请手动运行: python build_index_now.py")
        return False

if __name__ == '__main__':
    try:
        if main():
            print("\n" + "=" * 60)
            print("[OK] 完成！现在可以启动服务器:")
            print("  python start_rag_server.py")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[ERROR] 安装或构建失败，请检查错误信息")
            print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

