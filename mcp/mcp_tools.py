"""
MCP 工具包装器
可以直接集成到 LangChain Agent 中使用
"""

import os
import sqlite3
from typing import Dict, Any, Optional, List
import httpx
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import yaml

# 数据库路径
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'finance.db')

# HTTP API 基础 URL
API_BASE_URL = "http://localhost:5001"

# 邮件配置（从 config.yaml 读取）
def _load_email_config() -> Dict[str, Any]:
    """加载邮件配置"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('email', {})
    except Exception as e:
        print(f"警告：无法加载邮件配置: {e}")
        return {}

def get_db_connection():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"数据库不存在: {DB_PATH}，请先运行 python mcp/init_database.py")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== HTTP API 工具（同步版本，供 LangChain 使用）====================

def query_reimbursement_status_tool(
    employee_id: str,
    reimbursement_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    查询报销状态工具（供 LangChain 使用）
    
    查询指定员工的报销申请状态，包括待审批、已通过、已拒绝等状态。
    
    Args:
        employee_id: 员工工号，例如：E001
        reimbursement_id: 报销单号（可选），例如：R20240315001
        start_date: 开始日期（可选），格式：YYYY-MM-DD，例如：2024-03-01
        end_date: 结束日期（可选），格式：YYYY-MM-DD，例如：2024-03-31
        status: 状态过滤（可选），可选值：pending/approved/rejected/paid
    
    Returns:
        格式化的字符串结果
    """
    try:
        params = {"employee_id": employee_id}
        if reimbursement_id:
            params["reimbursement_id"] = reimbursement_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = httpx.get(
            f"{API_BASE_URL}/api/reimbursement/status",
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            return f"查询失败: {result.get('message', '未知错误')}"
        
        data = result.get("data", [])
        if status:
            status = status.lower()
            data = [item for item in data if (item.get("status") or "").lower() == status]
        total_amount = result.get("total_amount", 0)
        
        if not data:
            if status:
                return f"未找到员工 {employee_id} 状态为 {status} 的报销记录"
            return f"未找到员工 {employee_id} 的报销记录"
        
        output = f"员工 {data[0].get('employee_name', employee_id)} 的报销记录（共 {len(data)} 条，总计 {total_amount} 元）：\n\n"
        for record in data:
            status_map = {
                "pending": "待审批",
                "approved": "已通过",
                "rejected": "已拒绝",
                "paid": "已支付"
            }
            status_cn = status_map.get(record.get("status", ""), record.get("status", ""))
            output += f"• 报销单号：{record.get('reimbursement_id')}\n"
            output += f"  类别：{record.get('category')}\n"
            output += f"  金额：{record.get('amount')} 元\n"
            output += f"  状态：{status_cn}\n"
            output += f"  申请日期：{record.get('apply_date')}\n\n"
        
        return output
    except httpx.HTTPError as e:
        return f"HTTP请求失败: {str(e)}"
    except Exception as e:
        return f"查询失败: {str(e)}"

def query_reimbursement_summary_tool(
    employee_id: str,
    start_date: str,
    end_date: str,
    category: Optional[str] = None
) -> str:
    """
    查询报销金额统计工具（供 LangChain 使用）
    
    查询指定员工在指定时间范围内的报销总金额统计。
    
    Args:
        employee_id: 员工工号，例如：E001
        start_date: 开始日期，格式：YYYY-MM-DD，例如：2024-03-01
        end_date: 结束日期，格式：YYYY-MM-DD，例如：2024-03-31
        category: 报销类别（可选），例如：差旅费、餐费
    
    Returns:
        格式化的字符串结果
    """
    try:
        params = {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date
        }
        if category:
            params["category"] = category
        
        response = httpx.get(
            f"{API_BASE_URL}/api/reimbursement/summary",
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            return f"查询失败: {result.get('message', '未知错误')}"
        
        data = result.get("data", {})
        employee_name = data.get("employee_name", employee_id)
        total_amount = data.get("total_amount", 0)
        count = data.get("count", 0)
        by_category = data.get("by_category", {})
        by_status = data.get("by_status", {})
        
        output = f"员工 {employee_name} ({employee_id}) 在 {start_date} 至 {end_date} 期间的报销统计：\n\n"
        output += f"总金额：{total_amount} 元\n"
        output += f"报销单数：{count} 条\n\n"
        
        if by_category:
            output += "按类别统计：\n"
            for cat, amount in by_category.items():
                output += f"  • {cat}：{amount} 元\n"
            output += "\n"
        
        if by_status:
            status_map = {
                "pending": "待审批",
                "approved": "已通过",
                "rejected": "已拒绝",
                "paid": "已支付"
            }
            output += "按状态统计：\n"
            for status, count_val in by_status.items():
                status_cn = status_map.get(status, status)
                output += f"  • {status_cn}：{count_val} 条\n"
        
        return output
    except httpx.HTTPError as e:
        return f"HTTP请求失败: {str(e)}"
    except Exception as e:
        return f"查询失败: {str(e)}"

# ==================== 数据库工具（供 LangChain 使用）====================

def query_employee_info_tool(
    employee_id: Optional[str] = None,
    name: Optional[str] = None,
    department: Optional[str] = None
) -> str:
    """
    查询员工信息工具（供 LangChain 使用）
    
    从员工表中查询员工的基本信息，包括姓名、部门、职位等。
    
    Args:
        employee_id: 员工工号（可选），例如：E001
        name: 员工姓名（可选），用于模糊查询
        department: 部门名称（可选）
    
    Returns:
        格式化的字符串结果
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
        
        if not rows:
            conn.close()
            return "未找到匹配的员工信息"
        
        output = f"找到 {len(rows)} 条员工记录：\n\n"
        for row in rows:
            output += f"工号：{row['employee_id']}\n"
            output += f"姓名：{row['name']}\n"
            output += f"部门：{row['department']}\n"
            output += f"职位：{row['position']}\n"
            output += f"邮箱：{row['email']}\n"
            output += f"电话：{row['phone']}\n\n"
        
        conn.close()
        return output
    except Exception as e:
        return f"查询失败: {str(e)}"

def query_reimbursement_records_tool(
    employee_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    查询报销记录工具（供 LangChain 使用）
    
    从报销记录表中查询详细的报销记录信息。
    
    Args:
        employee_id: 员工工号
        start_date: 开始日期（可选），格式：YYYY-MM-DD
        end_date: 结束日期（可选），格式：YYYY-MM-DD
        status: 状态筛选（可选）：pending, approved, rejected, paid
        limit: 返回记录数限制，默认100
    
    Returns:
        格式化的字符串结果
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
        
        if not rows:
            conn.close()
            return f"未找到员工 {employee_id} 的报销记录"
        
        status_map = {
            "pending": "待审批",
            "approved": "已通过",
            "rejected": "已拒绝",
            "paid": "已支付"
        }
        
        output = f"员工 {employee_name} ({employee_id}) 的报销记录（共 {len(rows)} 条）：\n\n"
        for row in rows:
            status_cn = status_map.get(row["status"], row["status"])
            output += f"报销单号：{row['reimbursement_id']}\n"
            output += f"类别：{row['category']}\n"
            output += f"金额：{row['amount']} 元\n"
            output += f"说明：{row['description']}\n"
            output += f"状态：{status_cn}\n"
            output += f"申请日期：{row['apply_date']}\n"
            if row["approve_date"]:
                output += f"审批日期：{row['approve_date']}\n"
            output += "\n"
        
        conn.close()
        return output
    except Exception as e:
        return f"查询失败: {str(e)}"

def create_work_order_tool(
    title: str,
    assignee_id: str,
    description: Optional[str] = None,
    priority: str = "medium",
    category: Optional[str] = None,
    duplicate_reason: Optional[str] = None,
    request_id: Optional[str] = None,
    action: str = "auto"
) -> str:
    """
    创建工单任务工具（供 LangChain 使用）
    
    在数据库中创建一条工单或任务记录，模拟创建 Jira 工单。
    
    Args:
        title: 工单标题
        assignee_id: 负责人工号
        description: 工单描述（可选）
        priority: 优先级，可选值：low, medium, high, urgent，默认：medium
        category: 工单类别（可选），例如：财务、IT、人事
    
    Returns:
        格式化的字符串结果
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 支持姓名或工号
        employee = None
        if assignee_id.upper().startswith("E"):
            cursor.execute("SELECT employee_id, name FROM employees WHERE employee_id = ?", [assignee_id.upper()])
            employee = cursor.fetchone()
        if not employee:
            # 尝试按姓名精确匹配
            cursor.execute("SELECT employee_id, name FROM employees WHERE name = ?", [assignee_id])
            employee = cursor.fetchone()
        if not employee:
            conn.close()
            return f"员工 {assignee_id} 不存在，无法创建工单"
        assignee_id = employee["employee_id"]
        
        # 检查是否存在相同标题+负责人且未关闭的工单
        cursor.execute(
            """
            SELECT work_order_id, status, created_at
                   , priority, category, description
            FROM work_orders
            WHERE assignee_id = ? AND title = ? AND status IN ('open', 'in_progress')
            ORDER BY created_at DESC
            """,
            [assignee_id, title]
        )
        existing = cursor.fetchone()
        
        valid_actions = {"auto", "create_new", "update_existing"}
        action = (action or "auto").lower()
        if action not in valid_actions:
            conn.close()
            return f"action 参数无效：{action}，可选值：auto/create_new/update_existing。"
        
        if existing:
            existing_info = (
                "已存在匹配工单：\n"
                f"- 工单号：{existing['work_order_id']}\n"
                f"- 状态：{existing['status']}\n"
                f"- 负责人：{employee['name']} ({assignee_id})\n"
                f"- 优先级：{existing['priority']}\n"
                f"- 类别：{existing['category'] or '未设置'}\n"
                f"- 创建时间：{existing['created_at']}\n"
            )
            if action == "update_existing":
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                existing_desc = existing["description"] or ""
                note_parts = []
                if description:
                    note_parts.append(description)
                if duplicate_reason:
                    note_parts.append(f"重复原因：{duplicate_reason}")
                if request_id:
                    note_parts.append(f"关联请求：{request_id}")
                addition = ""
                if note_parts:
                    addition = f"[更新 {timestamp}] " + " ".join(note_parts)
                    new_description = f"{existing_desc}\n{addition}".strip()
                else:
                    new_description = existing_desc
                new_priority = priority or existing["priority"]
                new_category = category or existing["category"]
                cursor.execute(
                    """
                    UPDATE work_orders
                    SET description = ?, priority = ?, category = ?
                    WHERE work_order_id = ?
                    """,
                    [new_description or None, new_priority, new_category, existing["work_order_id"]]
                )
                conn.commit()
                conn.close()
                return (
                    f"✅ 已更新现有工单 {existing['work_order_id']}。\n"
                    f"{existing_info}"
                    "如需新增工单，可设置 action=\"create_new\" 并提供 duplicate_reason。"
                )
            elif action == "create_new" and not duplicate_reason:
                conn.close()
                return (
                    existing_info
                    + "已存在相同工单。如仍需创建新的工单，请提供 duplicate_reason 说明。"
                )
            elif action == "auto" and not duplicate_reason:
                conn.close()
                return (
                    existing_info
                    + "系统已阻止重复创建。\n"
                    "如需更新此工单，请设置 action=\"update_existing\" 并提供新的描述或优先级。\n"
                    "如确需新建，请设置 action=\"create_new\" 并提供 duplicate_reason。"
                )
        
        # 生成工单号
        from datetime import datetime
        from uuid import uuid4
        unique_suffix = uuid4().hex[:6].upper()
        work_order_id = f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}{unique_suffix}"
        
        # 如果提供了 request_id 或 duplicate_reason，将其写入描述便于追踪
        meta_lines = []
        if request_id:
            meta_lines.append(f"[RequestID: {request_id}]")
        if duplicate_reason:
            meta_lines.append(f"[DuplicateReason: {duplicate_reason}]")
        meta_text = "\n".join(meta_lines)
        final_description = description or ""
        if meta_text:
            final_description = f"{final_description}\n{meta_text}".strip()
        
        # 插入工单
        cursor.execute('''
            INSERT INTO work_orders 
            (work_order_id, title, description, assignee_id, priority, category, status)
            VALUES (?, ?, ?, ?, ?, ?, 'open')
        ''', [work_order_id, title, final_description or None, assignee_id, priority, category])
        
        conn.commit()
        conn.close()
        
        priority_map = {
            "low": "低",
            "medium": "中",
            "high": "高",
            "urgent": "紧急"
        }
        priority_cn = priority_map.get(priority, priority)
        
        extra_note = ""
        if duplicate_reason:
            extra_note = f"\n备注：重复工单原因 - {duplicate_reason}"
        if request_id:
            extra_note += f"\n关联请求：{request_id}"
        return (
            "✅ 工单创建成功！\n\n"
            f"工单号：{work_order_id}\n"
            f"标题：{title}\n"
            f"负责人：{employee['name']} ({assignee_id})\n"
            f"优先级：{priority_cn}\n"
            "状态：待处理"
            f"{extra_note}"
        )
    except Exception as e:
        return f"创建工单失败: {str(e)}"

# ==================== 邮件发送工具 ====================

def send_email_tool(
    to_email: str,
    subject: str,
    body: str,
    cc_email: Optional[str] = None,
    bcc_email: Optional[str] = None,
    is_html: bool = False
) -> str:
    """
    发送邮件工具（供 LangChain 使用）
    
    通过 SMTP 服务器发送邮件。支持纯文本和 HTML 格式。
    
    Args:
        to_email: 收件人邮箱地址，例如：zhangsan@company.com
        subject: 邮件主题
        body: 邮件正文内容
        cc_email: 抄送邮箱（可选），多个邮箱用逗号分隔
        bcc_email: 密送邮箱（可选），多个邮箱用逗号分隔
        is_html: 是否为 HTML 格式，默认 False（纯文本）
    
    Returns:
        格式化的字符串结果
    """
    try:
        # 加载邮件配置
        email_config = _load_email_config()
        
        if not email_config:
            return (
                "❌ 邮件发送失败：未配置邮件服务器。\n"
                "请在 config.yaml 中添加 email 配置，例如：\n"
                "email:\n"
                "  smtp_host: smtp.example.com\n"
                "  smtp_port: 587\n"
                "  smtp_user: your_email@example.com\n"
                "  smtp_password: your_password\n"
                "  from_email: your_email@example.com\n"
                "  from_name: 财务助手"
            )
        
        smtp_host = email_config.get('smtp_host')
        smtp_port = email_config.get('smtp_port', 587)
        smtp_user = email_config.get('smtp_user')
        smtp_password = email_config.get('smtp_password')
        from_email = email_config.get('from_email', smtp_user)
        from_name = email_config.get('from_name', '财务助手')
        use_tls = email_config.get('use_tls', True)
        
        if not smtp_host or not smtp_user:
            return "❌ 邮件发送失败：SMTP 服务器配置不完整（缺少 smtp_host 或 smtp_user）"
        
        # 创建邮件消息
        msg = MIMEMultipart('alternative')
        # From 头格式：使用 formataddr 确保符合 RFC 标准
        if from_name:
            msg['From'] = formataddr((from_name, from_email))
        else:
            msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        if cc_email:
            msg['Cc'] = cc_email
        
        # 添加邮件正文
        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 构建收件人列表（包括抄送和密送）
        recipients = [to_email]
        if cc_email:
            recipients.extend([email.strip() for email in cc_email.split(',')])
        if bcc_email:
            recipients.extend([email.strip() for email in bcc_email.split(',')])
        
        # 连接 SMTP 服务器并发送
        try:
            if smtp_port == 465:
                # SSL 连接
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                # TLS 连接
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                if use_tls:
                    server.starttls()
            
            if smtp_password:
                server.login(smtp_user, smtp_password)
            
            server.sendmail(from_email, recipients, msg.as_string())
            server.quit()
            
            recipient_list = to_email
            if cc_email:
                recipient_list += f", 抄送: {cc_email}"
            if bcc_email:
                recipient_list += f", 密送: {bcc_email}"
            
            return (
                f"✅ 邮件发送成功！\n\n"
                f"收件人：{recipient_list}\n"
                f"主题：{subject}\n"
                f"格式：{'HTML' if is_html else '纯文本'}\n"
                f"内容长度：{len(body)} 字符"
            )
        except smtplib.SMTPAuthenticationError:
            return "❌ 邮件发送失败：SMTP 认证失败，请检查用户名和密码"
        except smtplib.SMTPRecipientsRefused as e:
            return f"❌ 邮件发送失败：收件人地址被拒绝 - {str(e)}"
        except smtplib.SMTPServerDisconnected:
            return "❌ 邮件发送失败：SMTP 服务器连接断开"
        except Exception as e:
            return f"❌ 邮件发送失败：{str(e)}"
            
    except Exception as e:
        return f"❌ 邮件发送失败：{str(e)}"

