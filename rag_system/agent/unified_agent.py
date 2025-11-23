"""
统一财务助手 Agent - 整合 RAG + MCP 工具
支持多步骤推理和自动工具选择
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from rag_system.config import load_config, ConfigError
from rag_system.retriever.rag_retriever import RAGRetriever
from rag_system.agent.entity_extractor import EntityExtractor, ParameterValidator
from mcp.mcp_tools import (
    query_employee_info_tool,
    query_reimbursement_status_tool,
    query_reimbursement_summary_tool,
    query_reimbursement_records_tool,
    create_work_order_tool,
    send_email_tool
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolSpec:
    """工具规格"""
    name: str
    func: callable
    description: str
    category: str = "unknown"  # "rag", "mcp_db", "mcp_api", "generation"


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: int
    tool_name: str
    arguments: Dict[str, Any]
    dependencies: List[str] = None
    status: str = "pending"  # pending, running, success, failed
    result: Any = None
    error: str = None


class AgentError(Exception):
    """Agent 基础异常"""
    pass


class ParameterError(AgentError):
    """参数错误"""
    pass


class DataNotFoundError(AgentError):
    """数据不存在错误"""
    pass


class UnifiedFinancialAgent:
    """统一财务助手 Agent - 整合 RAG 和 MCP 工具"""
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        retriever: Optional[RAGRetriever] = None,
        verbose: bool = True,
        max_steps: int = 8,
        user_context: Optional[Dict] = None
    ):
        """
        初始化统一 Agent
        
        Args:
            config_path: 配置文件路径
            retriever: RAG 检索器（可选，会自动初始化）
            verbose: 是否打印详细日志
            max_steps: 最大工具调用步数
            user_context: 用户上下文（包含用户身份信息）
        """
        self.verbose = verbose
        self.max_steps = max_steps
        self.user_context = user_context or {}  # 用户上下文（V1.1新增）
        
        # 加载配置
        try:
            self.config = load_config(config_path)
        except ConfigError as e:
            raise ValueError(f"配置加载失败: {e}") from e
        
        # 初始化 RAG 检索器（使用混合检索）
        if retriever is None:
            self.retriever = RAGRetriever(use_hybrid=True)  # V1.1: 启用混合检索
            if not self.retriever.is_index_ready():
                logger.warning("RAG 索引未初始化，知识库检索功能将不可用")
        else:
            self.retriever = retriever
        
        # 初始化 LLM
        self._setup_llm()
        
        # 创建工具列表
        self.tools = self._create_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # 工具依赖图
        self.tool_dependencies = {
            "query_reimbursement_summary": ["query_employee_info"],
            "query_reimbursement_status": ["query_employee_info"],
            "query_reimbursement_records": ["query_employee_info"],
            "create_work_order": ["query_employee_info"],
            "send_email": ["query_employee_info"],  # 发送邮件前可能需要查询收件人信息
        }
        
        # 工具优先级（数字越小优先级越高）
        self.tool_priority = {
            "query_employee_info": 1,  # 最高优先级，获取基础数据
            "rag_search": 2,  # 获取规则
            "query_reimbursement_summary": 3,
            "query_reimbursement_status": 3,
            "query_reimbursement_records": 3,
            "create_work_order": 4,
            "send_email": 5,  # 最后发送邮件
        }
        
        # 初始化实体提取器和参数验证器（V1.1新增）
        self.entity_extractor = EntityExtractor(user_context=self.user_context)
        self.param_validator = ParameterValidator(self.entity_extractor)
    
    def _setup_llm(self):
        """设置 LLM"""
        llm_config = self.config['models']['llm']
        
        if llm_config['provider'] == 'tongyi':
            api_key = llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
            api_base = llm_config.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            os.environ['OPENAI_API_KEY'] = api_key
            os.environ['OPENAI_API_BASE'] = api_base
            self.llm = ChatOpenAI(
                model=llm_config.get('model_name', 'qwen-turbo'),
                temperature=0.1
            )
        else:
            api_key = llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = api_key
            self.llm = ChatOpenAI(
                model=llm_config.get('model_name', 'gpt-3.5-turbo'),
                temperature=0.1
            )
    
    def _create_tools(self) -> List[ToolSpec]:
        """创建工具列表（RAG + MCP）"""
        tools = []
        
        # RAG 知识库检索工具
        def rag_search_tool(query: str) -> str:
            """检索企业财务知识库，回答关于报销政策、财务制度、流程等问题"""
            if not self.retriever.is_index_ready():
                return "知识库索引未初始化，无法检索。请先运行: python -m rag_system.main index"
            
            try:
                result = self.retriever.retrieve(query, top_k=3)
                sources = result.get('sources', [])
                
                if not sources:
                    return "未找到相关制度文档"
                
                output = "检索到以下制度信息：\n\n"
                for i, source in enumerate(sources, 1):
                    doc_name = source.get('metadata', {}).get('file_name', '未知文档')
                    text = source.get('text', '')[:300]  # 限制长度
                    score = source.get('score', 0)
                    output += f"{i}. 【{doc_name}】\n"
                    output += f"   内容：{text}...\n"
                    output += f"   相关度：{score:.2f}\n\n"
                
                return output
            except Exception as e:
                return f"检索出错：{str(e)}"
        
        tools.append(ToolSpec(
            name="rag_search",
            func=rag_search_tool,
            description="检索企业财务知识库，查询报销政策、财务制度、流程规定等。输入应该是关于制度、规则的问题。",
            category="rag"
        ))
        
        # MCP 数据库工具
        tools.append(ToolSpec(
            name="query_employee_info",
            func=query_employee_info_tool,
            description="从员工表中查询员工的基本信息，包括姓名、部门、职位等。输入参数：employee_id（可选）、name（可选）、department（可选）。",
            category="mcp_db"
        ))
        
        tools.append(ToolSpec(
            name="query_reimbursement_status",
            func=query_reimbursement_status_tool,
            description="查询指定员工的报销申请状态。输入参数：employee_id（必需）、start_date（可选）、end_date（可选）、status（可选）。",
            category="mcp_api"
        ))
        
        tools.append(ToolSpec(
            name="query_reimbursement_summary",
            func=query_reimbursement_summary_tool,
            description="查询指定员工在指定时间范围内的报销总金额统计。输入参数：employee_id（必需）、start_date（必需）、end_date（必需）、category（可选）。",
            category="mcp_api"
        ))
        
        tools.append(ToolSpec(
            name="query_reimbursement_records",
            func=query_reimbursement_records_tool,
            description="从报销记录表中查询详细的报销记录信息。输入参数：employee_id（必需）、start_date（可选）、end_date（可选）、status（可选）。",
            category="mcp_db"
        ))
        
        tools.append(ToolSpec(
            name="create_work_order",
            func=create_work_order_tool,
            description="在数据库中创建一条工单或任务记录。输入参数：title（必需）、assignee_id（必需）、priority（可选）、category（可选）。",
            category="mcp_db"
        ))
        
        tools.append(ToolSpec(
            name="send_email",
            func=send_email_tool,
            description="通过 SMTP 服务器发送邮件。输入参数：to_email（必需，收件人邮箱）、subject（必需，邮件主题）、body（必需，邮件正文）、cc_email（可选，抄送）、bcc_email（可选，密送）、is_html（可选，是否为HTML格式，默认false）。",
            category="mcp_email"
        ))
        
        return tools
    
    def _understand_intent(self, user_input: str) -> Dict[str, Any]:
        """
        理解用户意图（V1.1增强版：支持用户上下文）
        
        Args:
            user_input: 用户输入
            
        Returns:
            意图分析结果
        """
        # 处理用户上下文（V1.1新增）
        processed_input = user_input
        if self.user_context:
            current_user = self.user_context.get('current_user', {})
            if current_user:
                # 替换"我"、"我的"等代词
                if "我" in processed_input or "我的" in processed_input:
                    user_name = current_user.get('name', '')
                    user_id = current_user.get('employee_id', '')
                    if user_name:
                        processed_input = processed_input.replace("我", user_name)
                        processed_input = processed_input.replace("我的", f"{user_name}的")
        
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description[:100]}..."
            for tool in self.tools
        ])
        
        user_context_str = ""
        if self.user_context and self.user_context.get('current_user'):
            current_user = self.user_context['current_user']
            user_context_str = f"""
用户上下文：
- 当前用户姓名: {current_user.get('name', '未知')}
- 当前用户工号: {current_user.get('employee_id', '未知')}
- 当前用户部门: {current_user.get('department', '未知')}

注意：如果用户输入中包含"我"、"我的"，请自动替换为当前用户信息。
"""
        
        prompt = f"""
你是一个智能财务助手，需要分析用户输入，识别任务类型和所需步骤。

可用工具：
{tools_desc}
{user_context_str}
用户输入：{processed_input}

请分析用户意图，返回 JSON 格式：
{{
    "intent_type": "complex_task|simple_query|content_generation",
    "requires_policy": true/false,  // 是否需要查询制度规则
    "requires_data": true/false,   // 是否需要查询数据
    "requires_generation": true/false,  // 是否需要生成内容（如邮件）
    "entities": {{
        "employee_name": "员工姓名（如果有，注意'我'应替换为当前用户）",
        "employee_id": "员工工号（如果有）",
        "date_range": "日期范围（如果有，如'3月份'应转换为具体日期）",
        "recipient": "收件人（如果有）",
        "topic": "主题/话题"
    }},
    "estimated_steps": 数字  // 预估需要多少步骤
}}

特别注意：
- "我"、"我的" → 需要替换为当前用户信息
- "3月份" → 转换为 start_date="2024-03-01", end_date="2024-03-31"
- "财务部" → 需要查询部门下的员工列表

只返回 JSON，不要其他文字。
"""
        
        try:
            response = self.llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            
            # 提取 JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_text = text[start:end]
                intent = json.loads(json_text)
            else:
                raise ValueError(f"无法解析意图：{text}")
            
            if self.verbose:
                logger.info(f"[Intent] {intent}")
            
            return intent
        except Exception as e:
            logger.error(f"意图理解失败: {e}")
            # 返回默认意图
            return {
                "intent_type": "simple_query",
                "requires_policy": True,
                "requires_data": False,
                "requires_generation": False,
                "entities": {},
                "estimated_steps": 2
            }
    
    def _generate_plan(self, intent: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """生成执行计划"""
        tools_desc = "\n".join([
            f"{idx+1}. {tool.name} (优先级:{self.tool_priority.get(tool.name, 99)}): {tool.description}"
            for idx, tool in enumerate(self.tools)
        ])
        
        history_text = "（暂无已执行步骤）"
        
        prompt = f"""
基于用户意图，生成详细的执行计划。

用户输入：{user_input}
用户意图：{json.dumps(intent, ensure_ascii=False)}

可用工具：
{tools_desc}

工具依赖关系：
- query_reimbursement_summary 依赖 query_employee_info
- query_reimbursement_status 依赖 query_employee_info
- create_work_order 依赖 query_employee_info
- generate_email 依赖 rag_search

已执行步骤：{history_text}

请生成执行计划，返回 JSON 格式：
{{
    "steps": [
        {{
            "step_id": 1,
            "tool_name": "工具名称",
            "arguments": {{"参数名": "参数值"}},
            "reason": "为什么需要这一步"
        }},
        ...
    ]
}}

规则：
1. 如果用户提供姓名但工具需要 employee_id，必须先调用 query_employee_info
2. 如果需要查询制度，调用 rag_search
3. 如果需要查询数据，调用相应的 MCP 工具
4. 如果需要生成内容，最后调用 LLM 生成
5. 考虑工具依赖关系，确保依赖的工具先执行

只返回 JSON，不要其他文字。
"""
        
        try:
            response = self.llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            
            # 提取 JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_text = text[start:end]
                plan = json.loads(json_text)
            else:
                raise ValueError(f"无法解析计划：{text}")
            
            # 验证和修正计划
            plan = self._validate_and_fix_plan(plan, intent)
            
            if self.verbose:
                logger.info(f"[Plan] {json.dumps(plan, ensure_ascii=False, indent=2)}")
            
            return plan
        except Exception as e:
            logger.error(f"计划生成失败: {e}")
            # 返回简单计划
            return {
                "steps": [
                    {
                        "step_id": 1,
                        "tool_name": "rag_search",
                        "arguments": {"query": user_input},
                        "reason": "查询相关制度"
                    }
                ]
            }
    
    def _validate_and_fix_plan(self, plan: Dict, intent: Dict) -> Dict:
        """
        验证和修正执行计划（V1.1增强版）
        
        检查项：
        1. 依赖关系完整性
        2. 重复步骤
        3. 参数完整性
        4. 步骤顺序合理性
        """
        steps = plan.get("steps", [])
        if not steps:
            return plan
        
        issues = []
        executed_tools = set()
        fixed_steps = []
        seen_steps = set()  # 用于检测重复步骤
        
        for i, step in enumerate(steps):
            tool_name = step.get("tool_name")
            if not tool_name:
                issues.append(f"步骤{i+1}缺少工具名称")
                continue
            
            if tool_name not in self.tool_map:
                issues.append(f"步骤{i+1}使用了未知工具: {tool_name}")
                continue
            
            # 检查重复步骤（相同工具+相同参数）
            step_key = (tool_name, str(sorted(step.get("arguments", {}).items())))
            if step_key in seen_steps:
                issues.append(f"步骤{i+1}与之前的步骤重复: {tool_name}")
                # 跳过重复步骤，但记录问题
                continue
            seen_steps.add(step_key)
            
            # 检查依赖关系
            deps = self.tool_dependencies.get(tool_name, [])
            for dep in deps:
                if dep not in executed_tools:
                    # 缺少依赖，自动插入
                    if dep == "query_employee_info":
                        # 尝试从 intent 中获取员工信息
                        entities = intent.get("entities", {})
                        employee_name = entities.get("employee_name")
                        employee_id = entities.get("employee_id")
                        
                        if employee_name and not employee_id:
                            # 检查是否已经有查询该员工的步骤
                            has_employee_query = any(
                                s.get("tool_name") == "query_employee_info" and
                                s.get("arguments", {}).get("name") == employee_name
                                for s in fixed_steps
                            )
                            
                            if not has_employee_query:
                                fixed_steps.append({
                                    "step_id": len(fixed_steps) + 1,
                                    "tool_name": "query_employee_info",
                                    "arguments": {"name": employee_name},
                                    "reason": f"获取员工工号，为 {tool_name} 做准备"
                                })
                                executed_tools.add("query_employee_info")
                                issues.append(f"自动添加依赖步骤: query_employee_info (为 {tool_name} 准备)")
            
            # 验证参数完整性（基本检查）
            arguments = step.get("arguments", {})
            if tool_name == "query_reimbursement_summary":
                if "employee_id" not in arguments and "name" not in arguments:
                    issues.append(f"步骤{i+1} ({tool_name}) 缺少必需参数: employee_id 或 name")
            
            fixed_steps.append(step)
            executed_tools.add(tool_name)
        
        # 重新编号
        for i, step in enumerate(fixed_steps, 1):
            step["step_id"] = i
        
        plan["steps"] = fixed_steps
        
        if self.verbose and issues:
            logger.warning(f"[Plan Validation] 发现 {len(issues)} 个问题:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        return plan
    
    def _resolve_dependencies(self, tool_name: str, context: Dict) -> List[str]:
        """解析工具依赖，返回需要先执行的工具列表"""
        deps = self.tool_dependencies.get(tool_name, [])
        resolved = []
        visited = set()
        
        def _resolve(tool: str):
            if tool in visited:
                return
            visited.add(tool)
            
            tool_deps = self.tool_dependencies.get(tool, [])
            for dep in tool_deps:
                _resolve(dep)
                if dep not in resolved:
                    resolved.append(dep)
            
            if tool not in resolved:
                resolved.append(tool)
        
        for dep in deps:
            _resolve(dep)
        
        return resolved
    
    def _execute_step(self, step: Dict, context: Dict) -> Tuple[bool, Any, Optional[str]]:
        """
        执行单个步骤（V1.1增强版：参数验证和修正）
        
        Args:
            step: 执行步骤
            context: 执行上下文
            
        Returns:
            (是否成功, 结果, 错误信息)
        """
        tool_name = step.get("tool_name")
        arguments = step.get("arguments", {})
        
        if tool_name not in self.tool_map:
            return False, None, f"未知工具: {tool_name}"
        
        tool = self.tool_map[tool_name]
        
        try:
            # V1.1: 使用参数验证器修正参数
            arguments = self.param_validator.validate_and_fix_params(
                tool_name, 
                arguments, 
                context
            )
            
            # 如果本次查询指定了姓名，记录在上下文
            if tool_name == "query_employee_info":
                if "name" in arguments and arguments.get("name"):
                    context["employee_name"] = arguments["name"]
            
            # 从 context 中补充参数（保留原有逻辑）
            def _normalize_identifier(value: Optional[str], context_key: str) -> Optional[str]:
                if context_key not in context:
                    return value
                if value is None:
                    return context[context_key]
                if isinstance(value, str):
                    normalized = value.strip()
                    if not normalized:
                        return context[context_key]
                    lower = normalized.lower()
                    if "employee_id" in lower or "工号" in normalized:
                        return context[context_key]
                    if normalized.upper().startswith("E") and normalized[1:].isdigit():
                        return normalized.upper()
                return value

            if "employee_id" in arguments:
                arguments["employee_id"] = _normalize_identifier(arguments.get("employee_id"), "employee_id")
            if "assignee_id" in arguments:
                arguments["assignee_id"] = _normalize_identifier(arguments.get("assignee_id"), "employee_id")
            
            # 调用工具
            result = tool.func(**arguments)
            
            # 提取关键信息到 context
            if tool_name == "query_employee_info":
                # 尝试从结果中提取 employee_id
                result_text = str(result)
                lines = result_text.split("\n")
                for line in lines:
                    if "工号：" in line:
                        employee_id = line.split("工号：")[1].strip().split()[0]
                        context["employee_id"] = employee_id
                        break
                for line in lines:
                    if "姓名：" in line:
                        employee_name = line.split("姓名：")[1].strip()
                        context["employee_name"] = employee_name
                        break
            
            return True, result, None
        except TypeError as e:
            error_msg = str(e)
            if "missing" in error_msg.lower() or "required" in error_msg.lower():
                return False, None, f"参数错误: {error_msg}"
            return False, None, f"调用工具参数错误: {error_msg}"
        except FileNotFoundError as e:
            return False, None, f"数据不存在: {str(e)}"
        except Exception as e:
            return False, None, f"调用工具失败: {str(e)}"
    
    def _execute_step_with_retry(
        self,
        step: Dict,
        context: Dict,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """执行步骤，带重试机制"""
        tool_name = step.get("tool_name")
        
        for attempt in range(max_retries + 1):
            success, result, error = self._execute_step(step, context)
            
            if success:
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1
                }
            
            # 如果是参数错误，尝试修正
            if "参数错误" in error or "missing" in error.lower():
                if attempt < max_retries:
                    # 尝试从 context 中补充参数
                    step = self._fix_parameters(step, error, context)
                    continue
            
            # 如果是数据不存在，提供建议
            if "数据不存在" in error or "不存在" in error:
                return {
                    "success": False,
                    "error": error,
                    "suggestion": self._generate_suggestion(tool_name, error),
                    "attempts": attempt + 1
                }
            
            # 其他错误，重试
            if attempt < max_retries:
                logger.warning(f"步骤 {step.get('step_id')} 失败，重试中... ({attempt + 1}/{max_retries})")
                continue
        
        return {
            "success": False,
            "error": error,
            "attempts": max_retries + 1
        }
    
    def _fix_parameters(self, step: Dict, error: str, context: Dict) -> Dict:
        """修正参数"""
        # 简单的参数修正逻辑
        arguments = step.get("arguments", {})
        
        # 如果缺少 employee_id，尝试从 context 获取
        if "employee_id" in arguments and not arguments.get("employee_id"):
            if "employee_id" in context:
                arguments["employee_id"] = context["employee_id"]
        if "assignee_id" in arguments and not arguments.get("assignee_id"):
            if "employee_id" in context:
                arguments["assignee_id"] = context["employee_id"]
        
        step["arguments"] = arguments
        return step
    
    def _generate_suggestion(self, tool_name: str, error: str) -> str:
        """生成错误建议"""
        suggestions = {
            "query_employee_info": "请检查员工姓名或工号是否正确",
            "query_reimbursement_summary": "请确认员工工号和日期范围是否正确",
            "rag_search": "知识库可能没有相关信息，请尝试其他关键词"
        }
        return suggestions.get(tool_name, "请检查输入参数是否正确")
    

    def _aggregate_results(
        self,
        question: str,
        results: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> str:
        """Aggregate outputs from RAG and MCP tools."""
        policy_info: List[str] = []
        data_info: List[str] = []
        other_info: List[str] = []

        for result in results:
            if not result.get("success"):
                continue

            tool_name = result.get("tool_name")
            tool_result = str(result.get("result", ""))

            if tool_name == "rag_search":
                policy_info.append(tool_result)
            elif tool_name in {
                "query_reimbursement_summary",
                "query_reimbursement_status",
                "query_reimbursement_records",
                "query_employee_info"
            }:
                data_info.append(tool_result)
            elif tool_name == "send_email":
                # 邮件发送结果单独处理，确保用户能看到发送状态
                other_info.append(f"[邮件发送] {tool_result}")
            else:
                other_info.append(tool_result)

        policy_text = "\\n\\n".join(policy_info) if policy_info else "(no policy info)"
        data_text = "\\n\\n".join(data_info) if data_info else "(no data info)"
        other_text = "\\n\\n".join(other_info) if other_info else "(none)"

        prompt = (
            "你是一个专业的财务助手。请基于以下信息回答用户问题。\\n\\n"
            f"用户问题：{question}\\n\\n"
            "制度/规则信息：\\n"
            f"{policy_text}\\n\\n"
            "数据信息：\\n"
            f"{data_text}\\n\\n"
            "其他信息：\\n"
            f"{other_text}\\n\\n"
            "要求：\\n"
            "1. 用中文回答，语言专业、友好\\n"
            "2. 如果用户需要发送邮件，请使用 send_email 工具实际发送（不要只生成内容）\\n"
            "3. 如果用户只需要生成邮件内容（不发送），请生成完整的内容\\n"
            "4. 明确引用信息来源（如\\\"根据《差旅费报销制度》...\\\"）\\n"
            "5. 如果信息不足，请说明并建议下一步操作\\n"
            "6. 如果用户询问是否符合条件，请基于规则和数据给出明确判断\\n\\n"
            "回答：\\n"
        )

        try:
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)
            return answer
        except Exception as e:
            logger.error(f"结果整合失败: {e}")
            return (
                "已获取以下信息：\\n\\n"
                f"制度信息：{policy_text[:200]}...\\n\\n"
                f"数据信息：{data_text[:200]}...\\n\\n"
                "请根据以上信息继续处理。"
            )


    def run(self, question: str) -> Dict[str, Any]:
        """
        执行多步骤推理
        
        Returns:
            {
                "answer": "最终回答",
                "steps": [...],  # 执行步骤详情
                "sources": [...]  # 信息来源
            }
        """
        if self.verbose:
            logger.info(f"[Question] {question}")
        
        # 步骤 1: 理解意图
        intent = self._understand_intent(question)
        
        # 步骤 2: 生成执行计划
        plan = self._generate_plan(intent, question)
        
        # 步骤 3: 执行计划
        context = {}  # 上下文信息，用于在步骤间传递数据
        execution_results = []
        steps_detail = []
        
        for step in plan.get("steps", [])[:self.max_steps]:
            step_id = step.get("step_id", len(steps_detail) + 1)
            tool_name = step.get("tool_name")
            
            if self.verbose:
                logger.info(f"[Step {step_id}] 执行工具: {tool_name}")
            
            # 执行步骤
            step_result = self._execute_step_with_retry(step, context)
            
            execution_result = {
                "step_id": step_id,
                "tool_name": tool_name,
                "arguments": step.get("arguments", {}),
                "success": step_result.get("success", False),
                "result": step_result.get("result"),
                "error": step_result.get("error"),
                "suggestion": step_result.get("suggestion")
            }
            
            execution_results.append(execution_result)
            steps_detail.append(execution_result)
            
            # 如果失败且是关键步骤，可以选择继续或停止
            if not step_result.get("success") and tool_name == "query_employee_info":
                # 员工信息查询失败，后续步骤可能无法执行
                if self.verbose:
                    logger.warning(f"关键步骤失败: {tool_name}")
        
        # 步骤 4: 整合结果
        final_answer = self._aggregate_results(question, execution_results, intent)
        
        # 提取来源信息
        sources = []
        for result in execution_results:
            if result.get("success") and result.get("tool_name") == "rag_search":
                sources.append({
                    "type": "policy",
                    "content": str(result.get("result", ""))[:200]
                })
        
        return {
            "answer": final_answer,
            "steps": steps_detail,
            "sources": sources,
            "intent": intent
        }

