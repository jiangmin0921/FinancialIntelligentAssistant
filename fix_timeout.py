"""
修复超时问题的脚本 - 切换到本地embedding模型
"""

import yaml
from pathlib import Path

def fix_config():
    """修复配置文件，切换到本地模型"""
    config_file = Path("config.yaml")
    
    if not config_file.exists():
        print("❌ config.yaml 不存在")
        return False
    
    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 修改embedding配置
    if config.get('models', {}).get('embedding', {}).get('provider') != 'local':
        print("正在修改配置，切换到本地embedding模型...")
        config['models']['embedding']['provider'] = 'local'
        config['models']['embedding']['model_name'] = 'BAAI/bge-small-zh-v1.5'
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print("✓ 配置已更新为使用本地embedding模型")
        print("\n提示:")
        print("  1. 首次运行需要下载模型（约100MB），请耐心等待")
        print("  2. 本地模型不需要API密钥，不会超时")
        print("  3. 现在可以重新运行: python quick_start.py")
        return True
    else:
        print("✓ 配置已经是本地模型，无需修改")
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("修复超时问题 - 切换到本地embedding模型")
    print("=" * 60)
    print()
    
    if fix_config():
        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
    else:
        print("\n修复失败，请检查配置文件")

