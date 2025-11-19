"""
MCP 工具测试脚本
直接测试各个工具的功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.mcp_tools import (
    query_employee_info_tool,
    query_reimbursement_status_tool,
    query_reimbursement_summary_tool,
    query_reimbursement_records_tool,
    create_work_order_tool
)

def test_query_employee_info():
    """测试查询员工信息"""
    print("=" * 60)
    print("测试 1: 查询员工信息")
    print("=" * 60)
    
    # 测试按工号查询
    result = query_employee_info_tool(employee_id="E001")
    print(result)
    print()
    
    # 测试按姓名查询
    result = query_employee_info_tool(name="张三")
    print(result)
    print()

def test_query_reimbursement_status():
    """测试查询报销状态"""
    print("=" * 60)
    print("测试 2: 查询报销状态（需要启动 mock_api_server.py）")
    print("=" * 60)
    
    try:
        result = query_reimbursement_status_tool(employee_id="E001")
        print(result)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("提示: 请先启动模拟 API 服务器: python mcp/mock_api_server.py")
    print()

def test_query_reimbursement_summary():
    """测试查询报销统计"""
    print("=" * 60)
    print("测试 3: 查询报销统计（需要启动 mock_api_server.py）")
    print("=" * 60)
    
    try:
        result = query_reimbursement_summary_tool(
            employee_id="E001",
            start_date="2024-03-01",
            end_date="2024-03-31"
        )
        print(result)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("提示: 请先启动模拟 API 服务器: python mcp/mock_api_server.py")
    print()

def test_query_reimbursement_records():
    """测试查询报销记录"""
    print("=" * 60)
    print("测试 4: 查询报销记录")
    print("=" * 60)
    
    result = query_reimbursement_records_tool(
        employee_id="E001",
        start_date="2024-03-01",
        end_date="2024-03-31"
    )
    print(result)
    print()

def test_create_work_order():
    """测试创建工单"""
    print("=" * 60)
    print("测试 5: 创建工单")
    print("=" * 60)
    
    result = create_work_order_tool(
        title="审核张三3月份报销申请",
        assignee_id="E004",
        description="需要审核张三在3月份的报销申请，包括差旅费和餐费",
        priority="high",
        category="财务"
    )
    print(result)
    print()

def test_integration_scenario():
    """测试集成场景：查询张三3月份的报销总金额"""
    print("=" * 60)
    print("测试 6: 集成场景 - 查询张三3月份的报销总金额")
    print("=" * 60)
    
    # 步骤1: 查询员工信息
    print("步骤1: 查询员工信息...")
    employee_info = query_employee_info_tool(name="张三")
    print(employee_info)
    print()
    
    # 步骤2: 查询报销统计
    print("步骤2: 查询报销统计...")
    try:
        summary = query_reimbursement_summary_tool(
            employee_id="E001",
            start_date="2024-03-01",
            end_date="2024-03-31"
        )
        print(summary)
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        print("提示: 请先启动模拟 API 服务器: python mcp/mock_api_server.py")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 MCP 工具测试")
    print("=" * 60 + "\n")
    
    # 检查数据库是否存在
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'finance.db')
    if not os.path.exists(db_path):
        print("⚠️  数据库不存在，请先运行: python mcp/init_database.py\n")
        sys.exit(1)
    
    # 运行测试
    test_query_employee_info()
    test_query_reimbursement_records()
    test_create_work_order()
    test_integration_scenario()
    
    # 需要 API 服务器的测试
    print("\n" + "=" * 60)
    print("⚠️  以下测试需要启动模拟 API 服务器")
    print("   运行命令: python mcp/mock_api_server.py")
    print("=" * 60 + "\n")
    
    test_query_reimbursement_status()
    test_query_reimbursement_summary()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

