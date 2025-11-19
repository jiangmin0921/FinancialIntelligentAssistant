"""
MCP Server 实现
提供 HTTP API 工具和数据库工具
"""

import asyncio
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
import httpx

# 尝试导入 MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False
    print("⚠️  MCP SDK 未安装，请运行: pip install mcp")

# 数据库路径
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'finance.db')

# HTTP API 基础 URL
API_BASE_URL = "http://localhost:5001"

# 创建 MCP Server 实例
if HAS_MCP_SDK:
    server = Server("financial-assistant-mcp")

def get_db_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"数据库不存在: {DB_PATH}，请先运行 python mcp/init_database.py")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== HTTP API 工具 ====================

async def query_reimbursement_status(
    employee_id: str,
    reimbursement_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询报销状态
    
    Args:
        employee_id: 员工工号
        reimbursement_id: 报销单号（可选）
        start_date: 开始日期（可选），格式：YYYY-MM-DD
        end_date: 结束日期（可选），格式：YYYY-MM-DD
    
    Returns:
        包含报销记录列表和总金额的字典
    """
    try:
        params = {"employee_id": employee_id}
        if reimbursement_id:
            params["reimbursement_id"] = reimbursement_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/reimbursement/status",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {
            "success": False,
            "message": f"HTTP请求失败: {str(e)}",
            "data": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": []
        }

async def query_reimbursement_summary(
    employee_id: str,
    start_date: str,
    end_date: str,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询报销金额统计
    
    Args:
        employee_id: 员工工号
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
        category: 报销类别（可选）
    
    Returns:
        包含统计信息的字典
    """
    try:
        params = {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date
        }
        if category:
            params["category"] = category
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/reimbursement/summary",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {
            "success": False,
            "message": f"HTTP请求失败: {str(e)}",
            "data": {}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": {}
        }

# ==================== 数据库工具 ====================

def query_employee_info(
    employee_id: Optional[str] = None,
    name: Optional[str] = None,
    department: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询员工信息
    
    Args:
        employee_id: 员工工号（可选）
        name: 员工姓名（可选，模糊查询）
        department: 部门名称（可选）
    
    Returns:
        包含员工信息的字典
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM employees WHERE 1=1"
        params = []
        
        if employee_id:
            query += " AND employee_id = ?"
            params.append(employee_id)
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        if department:
            query += " AND department = ?"
            params.append(department)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                "employee_id": row["employee_id"],
                "name": row["name"],
                "department": row["department"],
                "position": row["position"],
                "email": row["email"],
                "phone": row["phone"]
            })
        
        conn.close()
        
        return {
            "success": True,
            "data": data,
            "message": f"查询成功，找到 {len(data)} 条记录"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"查询失败: {str(e)}"
        }

def query_reimbursement_records(
    employee_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    查询报销记录
    
    Args:
        employee_id: 员工工号
        start_date: 开始日期（可选），格式：YYYY-MM-DD
        end_date: 结束日期（可选），格式：YYYY-MM-DD
        status: 状态筛选（可选）：pending, approved, rejected, paid
        limit: 返回记录数限制，默认100
    
    Returns:
        包含报销记录的字典
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取员工姓名
        cursor.execute("SELECT name FROM employees WHERE employee_id = ?", [employee_id])
        employee = cursor.fetchone()
        employee_name = employee["name"] if employee else "未知"
        
        # 构建查询
        query = '''
            SELECT 
                r.id,
                r.reimbursement_id,
                r.employee_id,
                r.amount,
                r.category,
                r.description,
                r.status,
                r.apply_date,
                r.approve_date
            FROM reimbursements r
            WHERE r.employee_id = ?
        '''
        params = [employee_id]
        
        if start_date:
            query += " AND r.apply_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND r.apply_date <= ?"
            params.append(end_date)
        
        if status:
            query += " AND r.status = ?"
            params.append(status)
        
        query += " ORDER BY r.apply_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                "id": row["id"],
                "reimbursement_id": row["reimbursement_id"],
                "employee_id": row["employee_id"],
                "employee_name": employee_name,
                "amount": row["amount"],
                "category": row["category"],
                "description": row["description"],
                "status": row["status"],
                "apply_date": row["apply_date"],
                "approve_date": row["approve_date"]
            })
        
        conn.close()
        
        return {
            "success": True,
            "data": data,
            "count": len(data),
            "message": f"查询成功，找到 {len(data)} 条记录"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": f"查询失败: {str(e)}"
        }

def create_work_order(
    title: str,
    assignee_id: str,
    description: Optional[str] = None,
    priority: str = "medium",
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建工单任务
    
    Args:
        title: 工单标题
        assignee_id: 负责人工号
        description: 工单描述（可选）
        priority: 优先级，可选值：low, medium, high, urgent，默认：medium
        category: 工单类别（可选），例如：财务、IT、人事
    
    Returns:
        包含创建的工单信息的字典
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证员工是否存在
        cursor.execute("SELECT employee_id FROM employees WHERE employee_id = ?", [assignee_id])
        if not cursor.fetchone():
            conn.close()
            return {
                "success": False,
                "message": f"员工 {assignee_id} 不存在"
            }
        
        # 生成工单号
        from datetime import datetime
        work_order_id = f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 插入工单
        cursor.execute('''
            INSERT INTO work_orders 
            (work_order_id, title, description, assignee_id, priority, category, status)
            VALUES (?, ?, ?, ?, ?, ?, 'open')
        ''', [work_order_id, title, description, assignee_id, priority, category])
        
        conn.commit()
        
        # 获取创建的工单
        cursor.execute('''
            SELECT work_order_id, title, status, created_at
            FROM work_orders
            WHERE work_order_id = ?
        ''', [work_order_id])
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "success": True,
            "data": {
                "work_order_id": row["work_order_id"],
                "title": row["title"],
                "status": row["status"],
                "created_at": row["created_at"]
            },
            "message": "工单创建成功"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"创建工单失败: {str(e)}"
        }

# ==================== 注册 MCP 工具 ====================

if HAS_MCP_SDK:
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """列出所有可用工具"""
        return [
            Tool(
                name="query_reimbursement_status",
                description="查询指定员工的报销申请状态，包括待审批、已通过、已拒绝等状态。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "员工工号，例如：E001"
                        },
                        "reimbursement_id": {
                            "type": "string",
                            "description": "报销单号（可选），例如：R20240315001"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期（可选），格式：YYYY-MM-DD，例如：2024-03-01"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期（可选），格式：YYYY-MM-DD，例如：2024-03-31"
                        }
                    },
                    "required": ["employee_id"]
                }
            ),
            Tool(
                name="query_reimbursement_summary",
                description="查询指定员工在指定时间范围内的报销总金额统计。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "员工工号，例如：E001"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期，格式：YYYY-MM-DD，例如：2024-03-01"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期，格式：YYYY-MM-DD，例如：2024-03-31"
                        },
                        "category": {
                            "type": "string",
                            "description": "报销类别（可选），例如：差旅费、餐费"
                        }
                    },
                    "required": ["employee_id", "start_date", "end_date"]
                }
            ),
            Tool(
                name="query_employee_info",
                description="从员工表中查询员工的基本信息，包括姓名、部门、职位等。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "员工工号，例如：E001"
                        },
                        "name": {
                            "type": "string",
                            "description": "员工姓名（可选），用于模糊查询"
                        },
                        "department": {
                            "type": "string",
                            "description": "部门名称（可选）"
                        }
                    }
                }
            ),
            Tool(
                name="query_reimbursement_records",
                description="从报销记录表中查询详细的报销记录信息。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "员工工号"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期，格式：YYYY-MM-DD"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期，格式：YYYY-MM-DD"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "approved", "rejected", "paid"],
                            "description": "状态筛选（可选）"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回记录数限制（可选），默认：100"
                        }
                    },
                    "required": ["employee_id"]
                }
            ),
            Tool(
                name="create_work_order",
                description="在数据库中创建一条工单或任务记录，模拟创建 Jira 工单。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "工单标题"
                        },
                        "description": {
                            "type": "string",
                            "description": "工单描述"
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "负责人工号"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "优先级"
                        },
                        "category": {
                            "type": "string",
                            "description": "工单类别，例如：财务、IT、人事"
                        }
                    },
                    "required": ["title", "assignee_id"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """调用工具"""
        try:
            if name == "query_reimbursement_status":
                result = await query_reimbursement_status(
                    employee_id=arguments.get("employee_id"),
                    reimbursement_id=arguments.get("reimbursement_id"),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
            elif name == "query_reimbursement_summary":
                result = await query_reimbursement_summary(
                    employee_id=arguments.get("employee_id"),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    category=arguments.get("category")
                )
            elif name == "query_employee_info":
                result = query_employee_info(
                    employee_id=arguments.get("employee_id"),
                    name=arguments.get("name"),
                    department=arguments.get("department")
                )
            elif name == "query_reimbursement_records":
                result = query_reimbursement_records(
                    employee_id=arguments.get("employee_id"),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    status=arguments.get("status"),
                    limit=arguments.get("limit", 100)
                )
            elif name == "create_work_order":
                result = create_work_order(
                    title=arguments.get("title"),
                    assignee_id=arguments.get("assignee_id"),
                    description=arguments.get("description"),
                    priority=arguments.get("priority", "medium"),
                    category=arguments.get("category")
                )
            else:
                result = {
                    "success": False,
                    "message": f"未知工具: {name}"
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "message": f"工具调用失败: {str(e)}"
                }, ensure_ascii=False)
            )]

# ==================== 主函数 ====================

async def main():
    """运行 MCP Server"""
    if not HAS_MCP_SDK:
        print("❌ MCP SDK 未安装")
        print("请运行: pip install mcp")
        return
    
    # 检查数据库
    if not os.path.exists(DB_PATH):
        print(f"⚠️  数据库不存在: {DB_PATH}")
        print("请先运行: python mcp/init_database.py")
        return
    
    print("🚀 MCP Server 启动中...")
    print(f"   数据库路径: {DB_PATH}")
    print(f"   API 地址: {API_BASE_URL}")
    print("=" * 50)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

