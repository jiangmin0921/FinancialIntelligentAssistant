"""
模拟报销系统 HTTP API 服务器
用于演示 MCP HTTP API 工具调用
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def index():
    """根路径说明"""
    return jsonify({
        'service': 'Mock Reimbursement API',
        'message': '可访问 /api/reimbursement/status, /api/reimbursement/summary, /api/health'
    })

# 数据库路径
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'finance.db')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/reimbursement/status', methods=['GET'])
def query_reimbursement_status():
    """查询报销状态"""
    employee_id = request.args.get('employee_id')
    reimbursement_id = request.args.get('reimbursement_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not employee_id:
        return jsonify({
            'success': False,
            'message': '缺少必需参数: employee_id'
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
            SELECT 
                r.reimbursement_id,
                r.employee_id,
                e.name as employee_name,
                r.amount,
                r.status,
                r.apply_date,
                r.category
            FROM reimbursements r
            JOIN employees e ON r.employee_id = e.employee_id
            WHERE r.employee_id = ?
        '''
        params = [employee_id]
        
        if reimbursement_id:
            query += ' AND r.reimbursement_id = ?'
            params.append(reimbursement_id)
        
        if start_date:
            query += ' AND r.apply_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND r.apply_date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY r.apply_date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 格式化结果
        data = []
        total_amount = 0.0
        for row in rows:
            record = {
                'reimbursement_id': row['reimbursement_id'],
                'employee_id': row['employee_id'],
                'employee_name': row['employee_name'],
                'amount': row['amount'],
                'status': row['status'],
                'apply_date': row['apply_date'],
                'category': row['category']
            }
            data.append(record)
            total_amount += row['amount']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'total_amount': round(total_amount, 2),
            'message': f'查询成功，找到 {len(data)} 条记录'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500

@app.route('/api/reimbursement/summary', methods=['GET'])
def query_reimbursement_summary():
    """查询报销金额统计"""
    employee_id = request.args.get('employee_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    
    if not employee_id or not start_date or not end_date:
        return jsonify({
            'success': False,
            'message': '缺少必需参数: employee_id, start_date, end_date'
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取员工信息
        cursor.execute('SELECT name FROM employees WHERE employee_id = ?', [employee_id])
        employee = cursor.fetchone()
        if not employee:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'员工 {employee_id} 不存在'
            }), 404
        
        employee_name = employee['name']
        
        # 构建查询
        query = '''
            SELECT 
                amount,
                category,
                status
            FROM reimbursements
            WHERE employee_id = ? AND apply_date >= ? AND apply_date <= ?
        '''
        params = [employee_id, start_date, end_date]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 统计
        total_amount = 0.0
        count = len(rows)
        by_category = {}
        by_status = {}
        
        for row in rows:
            amount = row['amount']
            cat = row['category']
            status = row['status']
            
            total_amount += amount
            
            by_category[cat] = by_category.get(cat, 0) + amount
            by_status[status] = by_status.get(status, 0) + 1
        
        # 格式化金额
        by_category = {k: round(v, 2) for k, v in by_category.items()}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'employee_id': employee_id,
                'employee_name': employee_name,
                'total_amount': round(total_amount, 2),
                'count': count,
                'by_category': by_category,
                'by_status': by_status
            },
            'message': '统计查询成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Mock Reimbursement API',
        'message': '服务运行正常'
    })

if __name__ == '__main__':
    # 确保数据库存在
    if not os.path.exists(DB_PATH):
        print("⚠️  数据库不存在，请先运行: python mcp/init_database.py")
    
    print("=" * 50)
    print("🚀 模拟报销系统 API 服务器启动")
    print("=" * 50)
    print("API地址: http://localhost:5001")
    print("健康检查: http://localhost:5001/api/health")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)

