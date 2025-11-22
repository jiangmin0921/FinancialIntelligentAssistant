"""
测试发送邮件给 HR 部门
"""

import os
import sys

# 设置 UTF-8 编码（Windows 控制台支持）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.mcp_tools import send_email_tool


def test_send_to_hr():
    """测试发送邮件给 HR 部门"""
    print("=" * 60)
    print("测试发送邮件给 HR 部门")
    print("=" * 60)
    
    to_email = "1546476756@qq.com"  # HR 部门邮箱
    subject = "差旅费报销申请"
    body = """
    尊敬的 HR 部门：

    您好！

    我想申请差旅费报销，具体情况如下：

    1. 申请类型：差旅费报销
    2. 出差时间：2024年3月
    3. 出差地点：北京
    4. 费用明细：
       - 交通费：800元
       - 住宿费：500元
       - 餐费：200元
       合计：1500元

    请您审核我的报销申请，如有需要补充的材料，请告知。

    谢谢！

    此致
    敬礼！

    张三
    财务部
    2024年3月20日
    """
    
    print(f"\n准备发送邮件：")
    print(f"  收件人：{to_email}")
    print(f"  主题：{subject}")
    print(f"  正文长度：{len(body)} 字符")
    
    # 调用邮件发送工具
    result = send_email_tool(
        to_email=to_email,
        subject=subject,
        body=body,
        is_html=False
    )
    
    print(f"\n发送结果：")
    print(result)


if __name__ == "__main__":
    print("\n[注意]")
    print("1. 请确保已在 config.yaml 中配置邮件服务器信息")
    print("2. 邮件将发送到：1546476756@qq.com")
    print("3. 发件人邮箱：2426199899@qq.com\n")
    
    try:
        test_send_to_hr()
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()

