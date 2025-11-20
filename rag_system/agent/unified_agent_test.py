"""
统一财务助手 Agent 测试用例
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag_system.agent.unified_agent import UnifiedFinancialAgent


def test_intent_understanding():
    """测试意图理解"""
    print("=" * 60)
    print("测试 1: 意图理解")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    
    test_cases = [
        "差旅费报销的标准是什么？",
        "帮我查一下张三 3 月份的报销总金额",
        "我想申请差旅报销，帮我确认下我是否符合报销条件，并帮我写一封发给 HR 的邮件。"
    ]
    
    for question in test_cases:
        print(f"\n问题: {question}")
        intent = agent._understand_intent(question)
        print(f"意图类型: {intent.get('intent_type')}")
        print(f"需要规则: {intent.get('requires_policy')}")
        print(f"需要数据: {intent.get('requires_data')}")
        print(f"需要生成: {intent.get('requires_generation')}")
        print(f"预估步骤: {intent.get('estimated_steps')}")


def test_plan_generation():
    """测试计划生成"""
    print("\n" + "=" * 60)
    print("测试 2: 计划生成")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    
    question = "我想申请差旅报销，帮我确认下我是否符合报销条件，并帮我写一封发给 HR 的邮件。"
    intent = agent._understand_intent(question)
    plan = agent._generate_plan(intent, question)
    
    print(f"\n问题: {question}")
    print(f"\n执行计划 ({len(plan.get('steps', []))} 步):")
    for step in plan.get('steps', []):
        print(f"  步骤{step['step_id']}: {step['tool_name']}")
        print(f"    原因: {step.get('reason', 'N/A')}")
        print(f"    参数: {step.get('arguments', {})}")


def test_tool_execution():
    """测试工具执行"""
    print("\n" + "=" * 60)
    print("测试 3: 工具执行")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    
    # 测试单个工具
    step = {
        "step_id": 1,
        "tool_name": "query_employee_info",
        "arguments": {"name": "张三"},
        "reason": "获取员工工号"
    }
    
    context = {}
    result = agent._execute_step_with_retry(step, context)
    
    print(f"\n工具: {step['tool_name']}")
    print(f"参数: {step['arguments']}")
    print(f"成功: {result.get('success')}")
    if result.get('success'):
        print(f"结果预览: {str(result.get('result', ''))[:200]}...")
        print(f"上下文更新: employee_id = {context.get('employee_id', 'N/A')}")
    else:
        print(f"错误: {result.get('error')}")


def test_full_workflow():
    """测试完整工作流"""
    print("\n" + "=" * 60)
    print("测试 4: 完整工作流")
    print("=" * 60)
    
    agent = UnifiedFinancialAgent(verbose=True)
    
    question = "帮我查一下张三 3 月份的报销总金额，并生成一段邮件说明。"
    result = agent.run(question)
    
    print(f"\n问题: {question}")
    print(f"\n执行了 {len(result['steps'])} 个步骤")
    print(f"\n最终回答:\n{result['answer']}")
    
    print(f"\n步骤详情:")
    for step in result['steps']:
        status = "✅" if step['success'] else "❌"
        print(f"  {status} {step['tool_name']}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 统一财务助手 Agent 测试")
    print("=" * 60)
    
    # 检查数据库
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'mcp', 'data', 'finance.db'
    )
    if not os.path.exists(db_path):
        print("⚠️  警告: MCP 数据库不存在")
        print(f"   请先运行: python mcp/init_database.py\n")
    
    try:
        test_intent_understanding()
        test_plan_generation()
        test_tool_execution()
        test_full_workflow()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

