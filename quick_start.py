"""
快速开始脚本 - 一键完成文档生成、索引构建和测试问答
"""

import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("财务助手 RAG 系统 - 快速开始")
    print("=" * 60)
    
    # 检查并提示设置镜像源
    import os
    hf_endpoint = os.getenv('HF_ENDPOINT', '')
    if not hf_endpoint:
        print("\n💡 提示: 如果下载模型时遇到网络超时，可以设置镜像源:")
        print("  Windows PowerShell: $env:HF_ENDPOINT='https://hf-mirror.com'")
        print("  Windows CMD: set HF_ENDPOINT=https://hf-mirror.com")
        print("  Linux/Mac: export HF_ENDPOINT=https://hf-mirror.com")
        print()
    
    # 检查依赖
    print("\n[1/4] 检查依赖...")
    try:
        import yaml
        print("  ✓ yaml")
    except ImportError:
        print("  ✗ 缺少依赖，请运行: pip install -r requirements.txt")
        return
    
    # 创建目录
    print("\n[2/4] 创建目录结构...")
    dirs = ["./data/documents", "./data/generated", "./data/vector_store"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}")
    
    # 生成文档
    print("\n[3/4] 生成财务文档...")
    try:
        from rag_system.data_generator.generate_docs import DocumentGenerator
        generator = DocumentGenerator()
        files = generator.generate_financial_documents()
        
        # 复制到documents目录
        import shutil
        import time
        for file in files:
            src = Path(file)
            dst = Path("./data/documents") / src.name
            
            # 如果目标文件存在，先尝试删除
            if dst.exists():
                try:
                    dst.unlink()  # 删除旧文件
                    print(f"  已删除旧文件: {dst.name}")
                except PermissionError:
                    print(f"  ⚠ 警告: 无法删除 {dst.name}，文件可能正在被其他程序打开")
                    print(f"  请关闭Word或其他打开此文件的程序，然后重试")
                    # 尝试重命名
                    try:
                        backup_name = dst.stem + "_backup_" + str(int(time.time())) + dst.suffix
                        backup_path = dst.parent / backup_name
                        dst.rename(backup_path)
                        print(f"  已重命名旧文件为: {backup_name}")
                    except Exception as e:
                        print(f"  ✗ 无法处理文件 {dst.name}: {e}")
                        continue
            
            # 复制文件
            try:
                shutil.copy2(src, dst)
                print(f"  ✓ 已复制: {dst.name}")
            except PermissionError as e:
                print(f"  ✗ 复制失败 {dst.name}: 权限被拒绝")
                print(f"  提示: 请确保文件未被其他程序打开，并检查目录权限")
                continue
            except Exception as e:
                print(f"  ✗ 复制失败 {dst.name}: {e}")
                continue
        
        print(f"  ✓ 已生成 {len(files)} 个文档")
    except Exception as e:
        print(f"  ✗ 文档生成失败: {e}")
        print("  提示: 需要安装 reportlab 和 python-docx")
        return
    
    # 构建索引
    print("\n[4/4] 构建向量索引...")
    try:
        from rag_system.retriever.rag_retriever import RAGRetriever
        # 创建retriever（此时索引不存在是正常的）
        retriever = RAGRetriever()
        # 构建索引
        retriever.build_index()
        
        # 验证索引是否构建成功
        if retriever.is_index_ready():
            print("  ✓ 索引构建完成并验证成功")
        else:
            print("  ⚠ 警告: 索引构建完成但验证失败")
            print("  尝试重新加载索引...")
            try:
                retriever.indexer.load_index()
                if retriever.is_index_ready():
                    print("  ✓ 索引重新加载成功")
                else:
                    raise RuntimeError("索引加载后仍不可用")
            except Exception as e2:
                print(f"  ✗ 索引加载失败: {e2}")
                raise
    except Exception as e:
        print(f"  ✗ 索引构建失败: {e}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        print("\n提示:")
        print("  1. 确保已安装: llama-index, chromadb, sentence-transformers")
        print("  2. 检查文档目录是否存在文档")
        print("  3. 如果使用本地embedding模型，确保网络连接正常")
        return
    
    print("\n" + "=" * 60)
    print("✓ 系统初始化完成！")
    print("\n下一步:")
    print("  运行问答: python -m rag_system.main qa")
    print("=" * 60)

if __name__ == "__main__":
    main()

