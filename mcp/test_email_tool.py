"""
测试邮件发送工具
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


def test_send_email():
    """测试邮件发送功能"""
    print("=" * 60)
    print("测试邮件发送工具")
    print("=" * 60)
    
    # 测试参数
    to_email = "1546476756@qq.com"  # 请替换为实际收件人邮箱
    subject = "测试邮件 - 财务助手"
    body = """
    这是一封测试邮件，用于验证财务助手的邮件发送功能。
    
    邮件内容：
    - 发件人：财务助手
    - 功能：自动发送报销申请、通知等邮件
    
    如果您收到这封邮件，说明邮件发送功能正常工作。
    
    谢谢！
    财务助手系统
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
    
    # 测试 HTML 邮件
    print("\n" + "=" * 60)
    print("测试 HTML 格式邮件")
    print("=" * 60)
    
    html_body = """
    <html>
    <body>
        <h2>测试邮件 - 财务助手</h2>
        <p>这是一封 <strong>HTML 格式</strong> 的测试邮件。</p>
        <ul>
            <li>功能：自动发送报销申请、通知等邮件</li>
            <li>支持：纯文本和 HTML 格式</li>
        </ul>
        <p>如果您收到这封邮件，说明邮件发送功能正常工作。</p>
        <p>谢谢！<br/>财务助手系统</p>
    </body>
    </html>
    """
    
    result_html = send_email_tool(
        to_email=to_email,
        subject="测试邮件 - HTML 格式",
        body=html_body,
        is_html=True
    )
    
    print(f"\n发送结果：")
    print(result_html)


if __name__ == "__main__":
    print("\n[注意]")
    print("1. 请确保已在 config.yaml 中配置邮件服务器信息")
    print("2. 请将测试邮箱地址替换为实际收件人邮箱")
    print("3. 某些邮件服务商需要授权码而非密码\n")
    
    try:
        test_send_email()
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()

