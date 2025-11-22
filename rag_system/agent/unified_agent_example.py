"""
统一财务助手 Agent 使用示例
演示多步骤推理和工具整合
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag_system.agent.unified_agent import UnifiedFinancialAgent


def example_1_simple_query():
    """示例 1: 简单查询 - 只查询制度"""
    print("=" * 60)
    print("示例 1: 简单查询 - 差旅费报销标准是什么？")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    result = agent.run("差旅费报销的标准是什么？")
    
    print("\n最终回答：")
    print(result["answer"])
    print("\n执行步骤：")
    for step in result["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"{status} 步骤{step['step_id']}: {step['tool_name']}")
        if not step["success"]:
            print(f"   错误: {step.get('error')}")


def example_2_data_query():
    """示例 2: 数据查询 - 查询员工报销情况"""
    print("\n" + "=" * 60)
    print("示例 2: 数据查询 - 查询张三3月份的报销总金额")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    result = agent.run("帮我查一下张三 3 月份的报销总金额")
    
    print("\n最终回答：")
    print(result["answer"])
    print("\n执行步骤：")
    for step in result["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"{status} 步骤{step['step_id']}: {step['tool_name']}")
        if step["success"] and step["tool_name"] == "query_employee_info":
            print(f"   结果预览: {str(step.get('result', ''))[:100]}...")


def example_3_complex_task():
    """示例 3: 复杂任务 - 制度查询 + 数据查询 + 内容生成"""
    print("\n" + "=" * 60)
    print("示例 3: 复杂任务 - 差旅报销申请（查询规则+数据+生成邮件）")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True, max_steps=8)
    
    question = "我想申请差旅报销，帮我确认下我是否符合报销条件，并帮我写一封发给 HR 的邮件。"
    result = agent.run(question)
    
    print("\n最终回答：")
    print(result["answer"])
    print("\n执行步骤详情：")
    for step in result["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"\n{status} 步骤{step['step_id']}: {step['tool_name']}")
        print(f"   参数: {step.get('arguments', {})}")
        if step["success"]:
            result_preview = str(step.get('result', ''))[:150]
            print(f"   结果预览: {result_preview}...")
        else:
            print(f"   错误: {step.get('error')}")
            if step.get('suggestion'):
                print(f"   建议: {step.get('suggestion')}")


def example_4_work_order():
    """示例 4: 创建工单"""
    print("\n" + "=" * 60)
    print("示例 4: 创建工单 - 审核报销申请")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    result = agent.run(
        "帮我创建一个工单，标题是'审核张三3月份报销申请'，分配给财务部的赵六，优先级设为高"
    )
    
    print("\n最终回答：")
    print(result["answer"])
    print("\n执行步骤：")
    for step in result["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"{status} 步骤{step['step_id']}: {step['tool_name']}")


def example_5_send_email():
    """示例 5: 发送邮件 - 报销申请邮件"""
    print("\n" + "=" * 60)
    print("示例 5: 发送邮件 - 发送差旅报销申请邮件给 HR")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True, max_steps=8)
    
    # 注意：实际发送邮件需要配置 config.yaml 中的 email 配置
    question = (
        "我想申请差旅报销，请帮我查询一下差旅费报销的标准，"
        "然后帮我写一封邮件发给 HR 部门（1546476756@qq.com），"
        "主题是'差旅费报销申请'，说明我想申请报销并询问具体流程。"
    )
    
    result = agent.run(question)
    
    print("\n最终回答：")
    print(result["answer"])
    print("\n执行步骤详情：")
    for step in result["steps"]:
        status = "✅" if step["success"] else "❌"
        print(f"\n{status} 步骤{step['step_id']}: {step['tool_name']}")
        if step["success"]:
            if step['tool_name'] == "send_email":
                print(f"   邮件发送结果: {str(step.get('result', ''))[:200]}")
            else:
                result_preview = str(step.get('result', ''))[:100]
                print(f"   结果预览: {result_preview}...")
        else:
            print(f"   错误: {step.get('error')}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 统一财务助手 Agent 使用示例")
    print("=" * 60 + "\n")
    
    # 检查数据库
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'mcp', 'data', 'finance.db'
    )
    if not os.path.exists(db_path):
        print("⚠️  警告: MCP 数据库不存在，部分功能可能不可用")
        print(f"   请先运行: python mcp/init_database.py\n")
    
    try:
        # 运行示例
        example_1_simple_query()
        example_2_data_query()
        example_3_complex_task()
        example_4_work_order()
        
        # 邮件发送示例（需要配置 SMTP）
        print("\n" + "⚠️  注意: 邮件发送功能需要配置 config.yaml 中的 email 设置")
        print("   如果未配置，示例 5 将显示配置提示\n")
        example_5_send_email()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例执行完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

