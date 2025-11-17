"""
修复文件权限问题 - 关闭可能被占用的文件
"""

import os
from pathlib import Path

def check_and_fix_files():
    """检查并修复文件权限问题"""
    print("=" * 60)
    print("检查文件权限问题")
    print("=" * 60)
    print()
    
    documents_dir = Path("./data/documents")
    generated_dir = Path("./data/generated")
    
    if not documents_dir.exists():
        print("✓ documents目录不存在，无需检查")
        return True
    
    print("检查以下目录中的文件:")
    print(f"  - {documents_dir}")
    print(f"  - {generated_dir}")
    print()
    
    problem_files = []
    
    # 检查documents目录
    if documents_dir.exists():
        for file in documents_dir.glob("*.docx"):
            try:
                # 尝试以写入模式打开文件
                with open(file, 'r+b') as f:
                    pass
                print(f"  ✓ {file.name} - 可访问")
            except PermissionError:
                problem_files.append(file)
                print(f"  ✗ {file.name} - 被占用或权限不足")
            except Exception as e:
                print(f"  ? {file.name} - {e}")
    
    # 检查generated目录
    if generated_dir.exists():
        for file in generated_dir.glob("*.docx"):
            try:
                with open(file, 'r+b') as f:
                    pass
                print(f"  ✓ {file.name} - 可访问")
            except PermissionError:
                problem_files.append(file)
                print(f"  ✗ {file.name} - 被占用或权限不足")
            except Exception as e:
                print(f"  ? {file.name} - {e}")
    
    if problem_files:
        print()
        print("=" * 60)
        print("发现以下文件可能被占用:")
        for file in problem_files:
            print(f"  - {file}")
        print()
        print("解决方案:")
        print("  1. 关闭所有打开这些文件的程序（如Word）")
        print("  2. 检查文件是否被其他进程锁定")
        print("  3. 如果不需要，可以删除这些文件后重新生成")
        print()
        
        choice = input("是否尝试删除这些文件？(y/n): ").strip().lower()
        if choice == 'y':
            for file in problem_files:
                try:
                    file.unlink()
                    print(f"  ✓ 已删除: {file.name}")
                except Exception as e:
                    print(f"  ✗ 无法删除 {file.name}: {e}")
            return True
        else:
            return False
    else:
        print()
        print("✓ 所有文件都可以正常访问")
        return True

if __name__ == '__main__':
    if check_and_fix_files():
        print()
        print("=" * 60)
        print("可以重新运行: python quick_start.py")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("请先解决文件占用问题，然后重新运行")
        print("=" * 60)

