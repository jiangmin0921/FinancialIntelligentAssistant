# MCP 工具测试用例

以下是 5 条自然语言指令，用于测试 AI 助理是否能自动决定调用相应的工具。

## 测试用例

### 测试用例 1
**指令**: "帮我查一下张三 3 月份的报销总金额，并生成一段邮件说明。"

**预期行为**:
1. 调用 `query_employee_info_tool` 查询员工"张三"的工号
2. 调用 `query_reimbursement_summary_tool` 查询该员工 2024-03-01 至 2024-03-31 的报销统计
3. 基于查询结果，生成邮件说明

**工具调用链**:
```
query_employee_info(name="张三") 
  → query_reimbursement_summary(employee_id="E001", start_date="2024-03-01", end_date="2024-03-31")
  → LLM 生成邮件内容
```

---

### 测试用例 2
**指令**: "查询一下《费用报销制度》的报销上限，然后帮我写个解释给领导。"

**预期行为**:
1. 调用 RAG 知识库检索工具（现有功能）查询《费用报销制度》文档
2. 提取报销上限信息
3. 生成给领导的解释说明

**工具调用链**:
```
knowledge_base_search("费用报销制度 报销上限")
  → LLM 生成解释说明
```

---

### 测试用例 3
**指令**: "帮我查一下李四的报销申请状态，看看有没有待审批的。"

**预期行为**:
1. 调用 `query_employee_info_tool` 查询员工"李四"的工号
2. 调用 `query_reimbursement_status_tool` 查询该员工的报销状态
3. 筛选出状态为"待审批"的记录

**工具调用链**:
```
query_employee_info(name="李四")
  → query_reimbursement_status(employee_id="E002")
  → 筛选 status="pending" 的记录
```

---

### 测试用例 4
**指令**: "查询 E001 员工在 3 月份的差旅费报销记录，并统计总金额。"

**预期行为**:
1. 调用 `query_reimbursement_records_tool` 查询 E001 员工 3 月份的报销记录
2. 筛选类别为"差旅费"的记录
3. 计算总金额并返回

**工具调用链**:
```
query_reimbursement_records(employee_id="E001", start_date="2024-03-01", end_date="2024-03-31")
  → 筛选 category="差旅费"
  → 计算总金额
```

---

### 测试用例 5
**指令**: "帮我创建一个工单，标题是'审核张三3月份报销申请'，分配给财务部的赵六，优先级设为高。"

**预期行为**:
1. 调用 `query_employee_info_tool` 查询"赵六"的工号和部门信息
2. 验证是否为财务部员工
3. 调用 `create_work_order_tool` 创建工单

**工具调用链**:
```
query_employee_info(name="赵六", department="财务部")
  → create_work_order(title="审核张三3月份报销申请", assignee_id="E004", priority="high", category="财务")
```

---

## 测试方法

### 方法 1: 使用 LangChain Agent 测试

```python
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from mcp.mcp_tools import (
    query_reimbursement_status_tool,
    query_reimbursement_summary_tool,
    query_employee_info_tool,
    query_reimbursement_records_tool,
    create_work_order_tool
)

# 创建工具列表
tools = [
    Tool(
        name="query_reimbursement_status",
        func=query_reimbursement_status_tool,
        description="查询指定员工的报销申请状态，包括待审批、已通过、已拒绝等状态。输入参数：employee_id（必需），reimbursement_id（可选），start_date（可选），end_date（可选）"
    ),
    Tool(
        name="query_reimbursement_summary",
        func=query_reimbursement_summary_tool,
        description="查询指定员工在指定时间范围内的报销总金额统计。输入参数：employee_id（必需），start_date（必需），end_date（必需），category（可选）"
    ),
    Tool(
        name="query_employee_info",
        func=query_employee_info_tool,
        description="从员工表中查询员工的基本信息，包括姓名、部门、职位等。输入参数：employee_id（可选），name（可选），department（可选）"
    ),
    Tool(
        name="query_reimbursement_records",
        func=query_reimbursement_records_tool,
        description="从报销记录表中查询详细的报销记录信息。输入参数：employee_id（必需），start_date（可选），end_date（可选），status（可选），limit（可选，默认100）"
    ),
    Tool(
        name="create_work_order",
        func=create_work_order_tool,
        description="在数据库中创建一条工单或任务记录。输入参数：title（必需），assignee_id（必需），description（可选），priority（可选，默认medium），category（可选）"
    )
]

# 初始化 Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 测试
result = agent.run("帮我查一下张三 3 月份的报销总金额，并生成一段邮件说明。")
print(result)
```

### 方法 2: 直接调用工具测试

```python
from mcp.mcp_tools import query_employee_info_tool, query_reimbursement_summary_tool

# 测试用例 1
employee_info = query_employee_info_tool(name="张三")
print(employee_info)

summary = query_reimbursement_summary_tool(
    employee_id="E001",
    start_date="2024-03-01",
    end_date="2024-03-31"
)
print(summary)
```

### 方法 3: 使用 MCP Server 测试

如果使用标准 MCP Server，可以通过 MCP 客户端连接测试：

```bash
# 启动 MCP Server
python mcp/mcp_server.py

# 在另一个终端使用 MCP 客户端测试
# （需要配置 MCP 客户端，如 Claude Desktop、Cursor 等）
```

## 预期结果

每个测试用例应该能够：
1. ✅ 正确识别需要调用的工具
2. ✅ 正确解析输入参数
3. ✅ 成功调用工具并获取结果
4. ✅ 基于工具返回结果生成最终回答
5. ✅ 处理错误情况（如员工不存在、数据库连接失败等）

