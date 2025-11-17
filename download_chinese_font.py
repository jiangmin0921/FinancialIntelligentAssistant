"""
下载中文字体用于PDF生成（如果系统没有中文字体）
"""

import os
import urllib.request
from pathlib import Path

def download_font():
    """下载开源中文字体"""
    font_dir = Path("./fonts")
    font_dir.mkdir(exist_ok=True)
    
    # 使用开源字体：思源黑体（Source Han Sans）
    # 这里提供一个简单的字体文件下载示例
    # 实际使用时，可以从Google Fonts或其他开源字体库下载
    
    font_urls = {
        "NotoSansCJK-Regular.ttc": "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansCN.zip"
    }
    
    print("=" * 60)
    print("下载中文字体")
    print("=" * 60)
    print("\n提示：")
    print("1. Windows系统通常自带中文字体，无需下载")
    print("2. 如果PDF仍有乱码，请检查系统字体路径")
    print("3. 可以手动下载字体文件到 ./fonts/ 目录")
    print("\n推荐的免费中文字体：")
    print("  - 思源黑体 (Source Han Sans)")
    print("  - 思源宋体 (Source Han Serif)")
    print("  - 文泉驿字体")
    print("\n下载地址：")
    print("  https://github.com/adobe-fonts/source-han-sans")
    print("=" * 60)

if __name__ == '__main__':
    download_font()

