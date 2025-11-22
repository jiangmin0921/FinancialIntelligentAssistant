"""
初始化 SQLite 数据库，创建表并插入示例数据
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta

# 设置 UTF-8 编码（Windows 控制台支持）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 数据库路径
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'finance.db')

def init_database():
    """初始化数据库"""
    # 创建目录
    os.makedirs(DB_DIR, exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建员工表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            position TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建报销记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reimbursements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reimbursement_id TEXT UNIQUE NOT NULL,
            employee_id TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            apply_date DATE,
            approve_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    ''')
    
    # 创建工单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            assignee_id TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            category TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignee_id) REFERENCES employees(employee_id)
        )
    ''')
    
    # 清空现有数据（可选，用于重置）
    cursor.execute('DELETE FROM work_orders')
    cursor.execute('DELETE FROM reimbursements')
    cursor.execute('DELETE FROM employees')
    
    # 插入示例员工数据
    employees = [
        ('E001', '张三', '财务部', '财务经理', '2426199899@qq.com', '13800138001'),
        ('E002', '李四', '技术部', '高级工程师', '2426199899@qq.com', '13800138002'),
        ('E003', '王五', '人事部', '人事专员', '2426199899@qq.com', '13800138003'),
        ('E004', '赵六', '财务部', '会计', '2426199899@qq.com', '13800138004'),
        ('E005', '钱七', '市场部', '市场经理', '2426199899@qq.com', '13800138005'),
    ]
    
    cursor.executemany('''
        INSERT INTO employees (employee_id, name, department, position, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', employees)
    
    # 插入示例报销记录
    today = datetime.now()
    reimbursements = [
        ('R20240315001', 'E001', 1500.00, '差旅费', '3月出差北京交通住宿费', 'approved', '2024-03-15', '2024-03-16'),
        ('R20240320002', 'E001', 800.00, '餐费', '3月客户招待餐费', 'pending', '2024-03-20', None),
        ('R20240310003', 'E002', 2000.00, '差旅费', '3月出差上海差旅费', 'approved', '2024-03-10', '2024-03-12'),
        ('R20240325004', 'E002', 500.00, '办公用品', '购买办公用品', 'rejected', '2024-03-25', '2024-03-26'),
        ('R20240305005', 'E003', 1200.00, '差旅费', '3月出差广州差旅费', 'paid', '2024-03-05', '2024-03-07'),
        ('R20240318006', 'E004', 600.00, '餐费', '部门聚餐费用', 'approved', '2024-03-18', '2024-03-19'),
        ('R20240322007', 'E005', 3000.00, '差旅费', '3月出差深圳差旅费', 'pending', '2024-03-22', None),
    ]
    
    cursor.executemany('''
        INSERT INTO reimbursements 
        (reimbursement_id, employee_id, amount, category, description, status, apply_date, approve_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', reimbursements)
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"[成功] 数据库初始化成功！")
    print(f"   数据库路径: {DB_PATH}")
    print(f"   已插入 {len(employees)} 条员工记录")
    print(f"   已插入 {len(reimbursements)} 条报销记录")

if __name__ == '__main__':
    init_database()

