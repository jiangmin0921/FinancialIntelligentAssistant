"""
设置HuggingFace镜像源 - 解决下载超时问题
"""

import os
import sys

def setup_mirror():
    """设置HuggingFace镜像源"""
    print("=" * 60)
    print("设置HuggingFace镜像源")
    print("=" * 60)
    print()
    print("由于网络问题，从HuggingFace下载模型可能超时。")
    print("可以使用国内镜像源加速下载。")
    print()
    print("可用的镜像源：")
    print("  1. https://hf-mirror.com (推荐，稳定)")
    print("  2. https://huggingface.co (官方，可能较慢)")
    print()
    
    choice = input("选择镜像源 (1/2，默认1): ").strip() or "1"
    
    if choice == "1":
        mirror_url = "https://hf-mirror.com"
        print(f"\n✓ 已设置镜像源: {mirror_url}")
    else:
        mirror_url = "https://huggingface.co"
        print(f"\n✓ 使用官方源: {mirror_url}")
    
    # 设置环境变量
    os.environ['HF_ENDPOINT'] = mirror_url
    
    print("\n提示：")
    print("  1. 这个设置只在当前会话有效")
    print("  2. 要永久设置，请添加到系统环境变量：")
    print(f"     HF_ENDPOINT={mirror_url}")
    print("  3. 或者在运行脚本前设置：")
    print(f"     set HF_ENDPOINT={mirror_url}  (Windows)")
    print(f"     export HF_ENDPOINT={mirror_url}  (Linux/Mac)")
    print()
    
    return mirror_url

def download_model_manually():
    """手动下载模型的说明"""
    print("=" * 60)
    print("手动下载模型")
    print("=" * 60)
    print()
    print("如果自动下载一直失败，可以手动下载：")
    print()
    print("方法1: 使用huggingface-cli")
    print("  pip install huggingface-hub")
    print("  huggingface-cli download BAAI/bge-small-zh-v1.5")
    print()
    print("方法2: 使用镜像源下载")
    print("  set HF_ENDPOINT=https://hf-mirror.com")
    print("  huggingface-cli download BAAI/bge-small-zh-v1.5")
    print()
    print("方法3: 使用git-lfs（如果已安装）")
    print("  git clone https://hf-mirror.com/BAAI/bge-small-zh-v1.5")
    print()

if __name__ == '__main__':
    setup_mirror()
    print()
    download_model_manually()

