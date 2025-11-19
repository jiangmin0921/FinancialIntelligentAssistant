"""
将 MCP 工具集成到 LangChain Agent 的示例
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dataclasses import dataclass
from typing import Callable, Dict, Any, List

from langchain_openai import ChatOpenAI
from rag_system.config import load_config

# 导入 MCP 工具
from mcp.mcp_tools import (
    query_reimbursement_status_tool,
    query_reimbursement_summary_tool,
    query_employee_info_tool,
    query_reimbursement_records_tool,
    create_work_order_tool
)


@dataclass
class ToolSpec:
    name: str
    func: Callable[..., str]
    description: str

def create_mcp_tools() -> List[ToolSpec]:
    """创建 MCP 工具列表"""
    tools = [
        ToolSpec(
            name="query_reimbursement_status",
            func=query_reimbursement_status_tool,
            description="""查询指定员工的报销申请状态，包括待审批、已通过、已拒绝等状态。
输入参数说明：
- employee_id (必需): 员工工号，例如：E001
- reimbursement_id (可选): 报销单号，例如：R20240315001
- start_date (可选): 开始日期，格式：YYYY-MM-DD，例如：2024-03-01
- end_date (可选): 结束日期，格式：YYYY-MM-DD，例如：2024-03-31
- status (可选): 状态过滤，例如：pending、approved、rejected、paid

使用示例：query_reimbursement_status(employee_id="E001", start_date="2024-03-01", end_date="2024-03-31")
"""
        ),
        ToolSpec(
            name="query_reimbursement_summary",
            func=query_reimbursement_summary_tool,
            description="""查询指定员工在指定时间范围内的报销总金额统计。
输入参数说明：
- employee_id (必需): 员工工号，例如：E001
- start_date (必需): 开始日期，格式：YYYY-MM-DD，例如：2024-03-01
- end_date (必需): 结束日期，格式：YYYY-MM-DD，例如：2024-03-31
- category (可选): 报销类别，例如：差旅费、餐费

使用示例：query_reimbursement_summary(employee_id="E001", start_date="2024-03-01", end_date="2024-03-31")
"""
        ),
        ToolSpec(
            name="query_employee_info",
            func=query_employee_info_tool,
            description="""从员工表中查询员工的基本信息，包括姓名、部门、职位等。
输入参数说明（至少提供一个）：
- employee_id (可选): 员工工号，例如：E001
- name (可选): 员工姓名，支持模糊查询，例如：张三
- department (可选): 部门名称，例如：财务部

使用示例：
- query_employee_info(employee_id="E001")
- query_employee_info(name="张三")
- query_employee_info(department="财务部")
"""
        ),
        ToolSpec(
            name="query_reimbursement_records",
            func=query_reimbursement_records_tool,
            description="""从报销记录表中查询详细的报销记录信息。
输入参数说明：
- employee_id (必需): 员工工号，例如：E001
- start_date (可选): 开始日期，格式：YYYY-MM-DD，例如：2024-03-01
- end_date (可选): 结束日期，格式：YYYY-MM-DD，例如：2024-03-31
- status (可选): 状态筛选，可选值：pending（待审批）、approved（已通过）、rejected（已拒绝）、paid（已支付）
- limit (可选): 返回记录数限制，默认100

使用示例：query_reimbursement_records(employee_id="E001", start_date="2024-03-01", end_date="2024-03-31", status="pending")
"""
        ),
        ToolSpec(
            name="create_work_order",
            func=create_work_order_tool,
            description="""在数据库中创建或更新工单。
输入参数说明：
- title (必需): 工单标题
- assignee_id (必需): 负责人工号或姓名（推荐使用工号）
- description (可选): 工单描述
- priority (可选): 优先级：low/medium/high/urgent
- category (可选): 工单类别
- duplicate_reason (可选): 若需重复创建，请说明原因
- request_id (可选): 外部请求编号
- action (可选): auto（默认，遇到重复时提示）、create_new（需配合 duplicate_reason）、update_existing（直接更新已有工单）

调用示例：
create_work_order(
    title="审核报销申请",
    assignee_id="赵六",
    priority="high",
    action="create_new",
    duplicate_reason="补录客户差旅单据",
    request_id="REQ-2024-03-001"
)
"""
        )
    ]
    return tools

class SimpleToolAgent:
    """不依赖 LangChain Agent 的工具调用示例"""
    
    def __init__(self, llm: ChatOpenAI, tools: List[ToolSpec], verbose: bool = True, max_steps: int = 4):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.verbose = verbose
        self.max_steps = max_steps
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "（暂无工具调用）"
        parts = []
        for idx, item in enumerate(history, 1):
            parts.append(
                f"步骤{idx}: 工具={item['tool_name']} 参数={json.dumps(item['arguments'], ensure_ascii=False)} 结果={item['result']}"
            )
        return "\n".join(parts)
    
    def _decide_tool(self, question: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        tools_desc = "\n".join(
            [f"{idx+1}. {tool.name}: {tool.description}" for idx, tool in enumerate(self.tools.values())]
        )
        prompt = f"""
你是一个智能助理，需要根据用户问题决定是否调用工具。工具列表如下：
{tools_desc}

请按以下格式返回决策（JSON）：
{{
  "tool_name": "<工具名称或 none>",
  "arguments": {{...}},
  "reason": "简要说明"
}}

用户问题：{question}

如果不需要工具，tool_name 设置为 "none"，arguments 为空对象。
"""
        rule_text = """
决策规则：
1. 如果用户提供姓名（如张三、李四）但工具需要 employee_id，请先调用 query_employee_info 获取工号，再调用其他工具。
2. 若缺少必填参数，优先调用可以补足参数的工具。
3. 如果无需工具即可回答，请选择 tool_name="none"，arguments={}。
""".strip()
        history_text = self._format_history(history)
        prompt = prompt.replace(
            "请按以下格式返回决策（JSON）：",
            f"已执行的工具调用：\n{history_text}\n\n请按以下格式返回决策（JSON）：",
            1
        )
        prompt = prompt.replace(
            "请按以下格式返回决策（JSON）：",
            f"{rule_text}\n\n请按以下格式返回决策（JSON）：",
            1
        )
        response = self.llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        try:
            decision = json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取 JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                snippet = text[start:end]
                decision = json.loads(snippet)
            else:
                raise ValueError(f"无法解析模型返回的JSON: {text}")
        if self.verbose:
            print("[Decision]", decision)
        return decision
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            return f"未知工具：{tool_name}"
        tool = self.tools[tool_name]
        try:
            return tool.func(**arguments)
        except TypeError as e:
            return f"调用工具参数错误: {e}"
        except Exception as e:
            return f"调用工具失败: {e}"
    
    def run(self, question: str) -> str:
        history: List[Dict[str, Any]] = []
        for _ in range(self.max_steps):
            decision = self._decide_tool(question, history)
            tool_name = decision.get("tool_name", "none")
            arguments = decision.get("arguments", {}) or {}
            
            if tool_name == "none":
                history_text = self._format_history(history)
                prompt = f"""
用户问题：{question}

以下是已执行的工具调用：
{history_text}

请基于已有信息给出最终回答；如信息不足，也请说明原因并提出下一步建议。
"""
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, "content") else str(response)
            
            tool_result = self._call_tool(tool_name, arguments)
            if self.verbose:
                print(f"[Tool Result] {tool_result}")
            history.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "result": tool_result
            })
        
        history_text = self._format_history(history)
        prompt = f"""
用户问题：{question}

已达到最大工具调用次数。现有信息如下：
{history_text}

请尽量给出答复，并说明可能的不足。
"""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)


def create_agent_with_mcp_tools(config_path: str = "config.yaml") -> SimpleToolAgent:
    """创建自定义的简易工具 Agent"""
    try:
        config = load_config(config_path)
        llm_config = config['models']['llm']
        
        # 初始化 LLM
        if llm_config['provider'] == 'tongyi':
            api_key = llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
            api_base = llm_config.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            os.environ['OPENAI_API_KEY'] = api_key
            os.environ['OPENAI_API_BASE'] = api_base
            llm = ChatOpenAI(
                model=llm_config.get('model_name', 'qwen-turbo'),
                temperature=0.1
            )
        else:
            api_key = llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = api_key
            llm = ChatOpenAI(
                model=llm_config.get('model_name', 'gpt-3.5-turbo'),
                temperature=0.1
            )
        
        tools = create_mcp_tools()
        return SimpleToolAgent(llm=llm, tools=tools, verbose=True)
    except Exception as e:
        print(f"❌ 创建 Agent 失败: {e}")
        raise

def main():
    """主函数：演示如何使用集成 MCP 工具的 Agent"""
    print("=" * 60)
    print("🚀 MCP 工具集成到 LangChain Agent 示例")
    print("=" * 60)
    print()
    
    # 检查数据库
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'finance.db')
    if not os.path.exists(db_path):
        print("⚠️  数据库不存在，请先运行: python mcp/init_database.py")
        return
    
    try:
        # 创建 Agent
        print("正在初始化 Agent...")
        agent = create_agent_with_mcp_tools()
        print("✅ Agent 初始化成功\n")
        
        # 测试用例
        test_cases = [
            "帮我查一下张三 3 月份的报销总金额，并生成一段邮件说明。",
            "查询一下 E001 员工的报销申请状态，看看有没有待审批的。",
            "帮我创建一个工单，标题是'审核张三3月份报销申请'，分配给财务部的赵六，优先级设为高。"
        ]
        
        for i, question in enumerate(test_cases, 1):
            print("=" * 60)
            print(f"测试用例 {i}: {question}")
            print("=" * 60)
            
            try:
                result = agent.run(question)
                print(f"\n✅ 回答:\n{result}\n")
            except Exception as e:
                print(f"\n❌ 处理失败: {e}\n")
            
            print()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

