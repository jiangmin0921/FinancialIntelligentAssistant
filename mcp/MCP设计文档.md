# MCP (Model Context Protocol) 设计文档

## 📋 概述

本文档描述了财务智能助手的 MCP 工具设计，使 AI 助理能够调用外部工具来执行实际业务操作。

## 🏗️ 架构图

```
┌─────────────────┐
│  LLM Client     │  (LangChain Agent / OpenAI Function Calling)
│  (AI Assistant) │
└────────┬────────┘
         │ MCP Protocol (JSON-RPC)
         │
         ▼
┌─────────────────┐
│  MCP Server     │  (Python MCP SDK)
│  (mcp_server.py)│
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ HTTP API     │  │ SQLite DB    │  │ File System  │
│ (报销系统)   │  │ (员工/报销)  │  │ (JSON文件)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 🔧 工具列表

### 工具 1: HTTP API 工具 - 报销系统接口

#### 1.1 查询报销状态 (query_reimbursement_status)

**描述**: 查询指定员工的报销申请状态，包括待审批、已通过、已拒绝等状态。

**输入参数 (Schema)**:
```json
{
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
```

**返回结构 (Schema)**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "请求是否成功"
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "reimbursement_id": {
            "type": "string",
            "description": "报销单号"
          },
          "employee_id": {
            "type": "string",
            "description": "员工工号"
          },
          "employee_name": {
            "type": "string",
            "description": "员工姓名"
          },
          "amount": {
            "type": "number",
            "description": "报销金额（元）"
          },
          "status": {
            "type": "string",
            "enum": ["pending", "approved", "rejected", "paid"],
            "description": "状态：pending-待审批, approved-已通过, rejected-已拒绝, paid-已支付"
          },
          "apply_date": {
            "type": "string",
            "description": "申请日期"
          },
          "category": {
            "type": "string",
            "description": "报销类别：差旅费、餐费、办公用品等"
          }
        }
      }
    },
    "total_amount": {
      "type": "number",
      "description": "总金额（元）"
    },
    "message": {
      "type": "string",
      "description": "返回消息"
    }
  }
}
```

#### 1.2 查询报销金额统计 (query_reimbursement_summary)

**描述**: 查询指定员工在指定时间范围内的报销总金额统计。

**输入参数 (Schema)**:
```json
{
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
```

**返回结构 (Schema)**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "data": {
      "type": "object",
      "properties": {
        "employee_id": {
          "type": "string"
        },
        "employee_name": {
          "type": "string"
        },
        "total_amount": {
          "type": "number",
          "description": "总金额（元）"
        },
        "count": {
          "type": "integer",
          "description": "报销单数量"
        },
        "by_category": {
          "type": "object",
          "description": "按类别统计",
          "additionalProperties": {
            "type": "number"
          }
        },
        "by_status": {
          "type": "object",
          "description": "按状态统计",
          "additionalProperties": {
            "type": "integer"
          }
        }
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

### 工具 2: 数据库工具 - SQLite 查询

#### 2.1 查询员工信息 (query_employee_info)

**描述**: 从员工表中查询员工的基本信息，包括姓名、部门、职位等。

**输入参数 (Schema)**:
```json
{
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
```

**返回结构 (Schema)**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "employee_id": {
            "type": "string",
            "description": "员工工号"
          },
          "name": {
            "type": "string",
            "description": "员工姓名"
          },
          "department": {
            "type": "string",
            "description": "部门"
          },
          "position": {
            "type": "string",
            "description": "职位"
          },
          "email": {
            "type": "string",
            "description": "邮箱"
          },
          "phone": {
            "type": "string",
            "description": "电话"
          }
        }
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

#### 2.2 查询报销记录 (query_reimbursement_records)

**描述**: 从报销记录表中查询详细的报销记录信息。

**输入参数 (Schema)**:
```json
{
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
```

**返回结构 (Schema)**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "description": "记录ID"
          },
          "reimbursement_id": {
            "type": "string",
            "description": "报销单号"
          },
          "employee_id": {
            "type": "string"
          },
          "employee_name": {
            "type": "string"
          },
          "amount": {
            "type": "number"
          },
          "category": {
            "type": "string"
          },
          "description": {
            "type": "string",
            "description": "报销说明"
          },
          "status": {
            "type": "string"
          },
          "apply_date": {
            "type": "string"
          },
          "approve_date": {
            "type": "string",
            "description": "审批日期（如果有）"
          }
        }
      }
    },
    "count": {
      "type": "integer",
      "description": "记录总数"
    },
    "message": {
      "type": "string"
    }
  }
}
```

#### 2.3 创建工单任务 (create_work_order)

**描述**: 在数据库中创建一条工单或任务记录，模拟创建 Jira 工单。

**输入参数 (Schema)**:
```json
{
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
```

**返回结构 (Schema)**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "data": {
      "type": "object",
      "properties": {
        "work_order_id": {
          "type": "string",
          "description": "工单号"
        },
        "title": {
          "type": "string"
        },
        "status": {
          "type": "string",
          "description": "状态：open-待处理"
        },
        "created_at": {
          "type": "string",
          "description": "创建时间"
        }
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

## 📊 数据库结构

### employees 表
```sql
CREATE TABLE employees (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT,
    position TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### reimbursements 表
```sql
CREATE TABLE reimbursements (
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
);
```

### work_orders 表
```sql
CREATE TABLE work_orders (
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
);
```

## 🔌 HTTP API 端点

### 报销系统 API (运行在 http://localhost:5001)

- `GET /api/reimbursement/status?employee_id={id}&start_date={date}&end_date={date}` - 查询报销状态
- `GET /api/reimbursement/summary?employee_id={id}&start_date={date}&end_date={date}&category={cat}` - 查询报销统计

## 🚀 使用流程

1. **启动 MCP Server**: `python mcp/mcp_server.py`
2. **启动模拟 HTTP API**: `python mcp/mock_api_server.py`
3. **初始化数据库**: `python mcp/init_database.py`
4. **在 LangChain Agent 中集成 MCP 工具**
5. **测试工具调用**: 使用测试用例验证功能

## 📝 注意事项

- MCP Server 使用 Python MCP SDK 实现
- 所有工具都支持中文输入和输出
- 数据库使用 SQLite，文件位于 `mcp/data/finance.db`
- HTTP API 是模拟服务，用于演示工具调用能力

