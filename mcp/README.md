# MCP (Model Context Protocol) 工具实现

本目录包含财务智能助手的 MCP 工具实现，使 AI 助理能够调用外部工具执行实际业务操作。

## 📁 文件结构

```
mcp/
├── README.md                    # 本文件
├── MCP设计文档.md               # MCP 工具设计文档
├── init_database.py             # 数据库初始化脚本
├── mock_api_server.py           # 模拟报销系统 HTTP API 服务器
├── mcp_server.py                # MCP Server 实现（标准 MCP 协议）
├── mcp_tools.py                 # MCP 工具包装器（供 LangChain 使用）
├── integrate_with_langchain.py   # LangChain Agent 集成示例
├── test_cases.md                # 测试用例说明
├── test_mcp_tools.py            # 工具测试脚本
└── data/                        # 数据目录
    └── finance.db               # SQLite 数据库（运行 init_database.py 后生成）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python mcp/init_database.py
```

这将创建 SQLite 数据库并插入示例数据（员工、报销记录等）。

### 3. 启动模拟 API 服务器（可选）

如果需要测试 HTTP API 工具，需要启动模拟 API 服务器：

```bash
python mcp/mock_api_server.py
```

服务器将在 `http://localhost:5001` 启动。

### 4. 测试工具

```bash
# 测试所有工具
python mcp/test_mcp_tools.py
```

### 5. 集成到 LangChain Agent

```bash
python mcp/integrate_with_langchain.py
```

## 🔧 工具列表

### HTTP API 工具

1. **query_reimbursement_status** - 查询报销状态
   - 通过 HTTP API 查询员工的报销申请状态

2. **query_reimbursement_summary** - 查询报销统计
   - 通过 HTTP API 查询员工的报销总金额统计

### 数据库工具

3. **query_employee_info** - 查询员工信息
   - 从 SQLite 数据库查询员工基本信息

4. **query_reimbursement_records** - 查询报销记录
   - 从 SQLite 数据库查询详细的报销记录

5. **create_work_order** - 创建工单
   - 在数据库中创建工单/任务记录

## 📝 使用示例

### 在 LangChain Agent 中使用

```python
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from mcp.mcp_tools import query_employee_info_tool, query_reimbursement_summary_tool

# 创建工具
tools = [
    Tool(
        name="query_employee_info",
        func=query_employee_info_tool,
        description="查询员工信息"
    ),
    Tool(
        name="query_reimbursement_summary",
        func=query_reimbursement_summary_tool,
        description="查询报销统计"
    )
]

# 创建 Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# 使用
result = agent.run("帮我查一下张三 3 月份的报销总金额")
```

### 直接调用工具

```python
from mcp.mcp_tools import query_employee_info_tool, query_reimbursement_summary_tool

# 查询员工信息
employee_info = query_employee_info_tool(name="张三")
print(employee_info)

# 查询报销统计
summary = query_reimbursement_summary_tool(
    employee_id="E001",
    start_date="2024-03-01",
    end_date="2024-03-31"
)
print(summary)
```

## 🧪 测试用例

参见 `test_cases.md` 文件，包含 5 条自然语言测试指令：

1. "帮我查一下张三 3 月份的报销总金额，并生成一段邮件说明。"
2. "查询一下《费用报销制度》的报销上限，然后帮我写个解释给领导。"
3. "帮我查一下李四的报销申请状态，看看有没有待审批的。"
4. "查询 E001 员工在 3 月份的差旅费报销记录，并统计总金额。"
5. "帮我创建一个工单，标题是'审核张三3月份报销申请'，分配给财务部的赵六，优先级设为高。"

## 📊 数据库结构

### employees 表
- employee_id (主键)
- name, department, position, email, phone

### reimbursements 表
- id (主键)
- reimbursement_id (唯一)
- employee_id, amount, category, description
- status, apply_date, approve_date

### work_orders 表
- id (主键)
- work_order_id (唯一)
- title, description, assignee_id
- priority, category, status

## 🔌 API 端点

模拟 API 服务器提供以下端点：

- `GET /api/reimbursement/status` - 查询报销状态
- `GET /api/reimbursement/summary` - 查询报销统计
- `GET /api/health` - 健康检查

## 📖 详细文档

- **MCP设计文档.md** - 完整的工具设计文档，包含参数 Schema、返回结构等
- **test_cases.md** - 详细的测试用例说明

## ⚠️ 注意事项

1. 数据库文件位于 `mcp/data/finance.db`，运行 `init_database.py` 后会自动创建
2. HTTP API 工具需要先启动 `mock_api_server.py`
3. 所有工具都支持中文输入和输出
4. 工具函数返回格式化的字符串，便于 LLM 理解和使用

## 🔄 与现有 RAG 系统集成

MCP 工具可以与现有的 RAG 系统（知识库检索）一起使用：

```python
from rag_system.agent.langchain_agent import FinancialAgent
from mcp.mcp_tools import create_mcp_tools

# 在 FinancialAgent 中添加 MCP 工具
agent = FinancialAgent()
agent.tools.extend(create_mcp_tools())
```

这样 AI 助理既能回答知识库问题，又能调用工具执行实际操作。

