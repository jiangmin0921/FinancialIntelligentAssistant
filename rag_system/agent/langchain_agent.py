"""
使用LangChain进行Agent编排
"""

import os
from typing import List, Dict, Any

from rag_system.config import ConfigError, load_config

# 检查LangChain Agent相关包（可选，用于完整Agent功能）
try:
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools import Tool
    HAS_LANGCHAIN_AGENT = True
except ImportError:
    HAS_LANGCHAIN_AGENT = False

# 检查LangChain LLM相关包（必需，用于SimpleRAGAgent）
try:
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN_OPENAI = True
except ImportError:
    HAS_LANGCHAIN_OPENAI = False

try:
    from langchain_community.llms import Tongyi
    HAS_LANGCHAIN_TONGYI = True
except ImportError:
    HAS_LANGCHAIN_TONGYI = False

# 如果都没有，打印警告
if not (HAS_LANGCHAIN_OPENAI or HAS_LANGCHAIN_TONGYI):
    print("警告: langchain相关包未安装")
    print("请运行: pip install langchain-openai langchain-community")


def _mask_key(key: str, visible: int = 4) -> str:
    """Mask sensitive API keys when printing debug logs."""
    if not key:
        return "None"
    if len(key) <= visible * 2:
        return "***masked***"
    return f"{key[:visible]}...{key[-visible:]}"


class FinancialAgent:
    """财务助手Agent"""
    
    def __init__(self, config_path: str = "config.yaml", retriever=None):
        """初始化Agent"""
        try:
            self.config = load_config(config_path)
        except ConfigError as exc:
            raise ValueError(f"配置加载失败: {exc}") from exc
        
        self.retriever = retriever
        self._setup_llm()
        self._setup_tools()
        self._setup_agent()
    
    def _setup_llm(self):
        """设置LLM模型"""
        llm_config = self.config['models']['llm']
        api_key_preview = _mask_key(llm_config.get('api_key'))
        print(f"[DEBUG] 初始化FinancialAgent LLM，provider={llm_config['provider']}, api_key={api_key_preview}")
        if llm_config['provider'] == 'tongyi':
            # 使用通义千问
            try:
                self.llm = Tongyi(
                    model_name=llm_config['model_name'],
                    dashscope_api_key=llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY'),
                    temperature=0.1
                )
            except:
                # 如果没有通义千问，使用OpenAI兼容接口
                api_key = llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
                api_base = llm_config.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
                # 直接使用环境变量（最可靠）
                os.environ['OPENAI_API_KEY'] = api_key
                os.environ['OPENAI_API_BASE'] = api_base
                self.llm = ChatOpenAI(
                    model="qwen-turbo",
                    temperature=0.1
                )
        else:
            # 使用OpenAI兼容接口 - 直接使用环境变量
            api_key = llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = api_key
            self.llm = ChatOpenAI(
                model=llm_config.get('model_name', 'gpt-3.5-turbo'),
                temperature=0.1
            )
    
    def _setup_tools(self):
        """设置工具"""
        def knowledge_base_search(query: str) -> str:
            """知识库检索工具"""
            if self.retriever is None:
                return "检索器未初始化"
            
            try:
                result = self.retriever.retrieve(query)
                # 格式化检索结果
                formatted_result = f"检索到以下相关信息：\n\n"
                for i, item in enumerate(result.get('sources', []), 1):
                    doc_name = item.get('metadata', {}).get('file_name', '未知文档')
                    text = item.get('text', '')[:200]  # 限制长度
                    formatted_result += f"{i}. 来源：{doc_name}\n   内容：{text}...\n\n"
                return formatted_result
            except Exception as e:
                return f"检索出错：{str(e)}"
        
        self.tools = [
            Tool(
                name="knowledge_base_search",
                func=knowledge_base_search,
                description="用于检索企业财务知识库，回答关于报销政策、财务制度、流程等问题。输入应该是用户的问题。"
            )
        ]
    
    def _setup_agent(self):
        """设置Agent"""
        if not HAS_LANGCHAIN_AGENT:
            self.agent = None
            return
        
        try:
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True
            )
        except Exception as e:
            print(f"Agent初始化失败: {e}")
            self.agent = None
    
    def query(self, question: str) -> Dict[str, Any]:
        """使用Agent回答问题"""
        if self.agent is None:
            # 如果Agent未初始化，直接使用检索器
            if self.retriever:
                result = self.retriever.retrieve(question)
                # 使用LLM生成回答
                context = "\n\n".join([
                    f"来源：{s.get('metadata', {}).get('file_name', '未知')}\n内容：{s.get('text', '')}"
                    for s in result.get('sources', [])[:3]
                ])
                
                prompt = f"""基于以下文档内容回答用户问题。如果文档中没有相关信息，请说明。

文档内容：
{context}

用户问题：{question}

请用中文回答，并在回答中引用文档来源。"""
                
                if hasattr(self.llm, 'invoke'):
                    response = self.llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                else:
                    answer = self.llm(prompt)
                
                return {
                    'answer': answer,
                    'sources': result.get('sources', [])
                }
            else:
                return {
                    'answer': '系统未正确初始化',
                    'sources': []
                }
        
        # 使用Agent
        try:
            answer = self.agent.run(question)
            # 获取检索来源
            sources = []
            if self.retriever:
                result = self.retriever.retrieve(question)
                sources = result.get('sources', [])
            
            return {
                'answer': answer,
                'sources': sources
            }
        except Exception as e:
            return {
                'answer': f'处理问题时出错：{str(e)}',
                'sources': []
            }


class SimpleRAGAgent:
    """简化版RAG Agent（不依赖LangChain Agent框架）"""
    
    def __init__(self, config_path: str = "config.yaml", retriever=None):
        """初始化简化Agent"""
        try:
            self.config = load_config(config_path)
        except ConfigError as exc:
            raise ValueError(f"配置加载失败: {exc}") from exc
        
        self.retriever = retriever
        self._setup_llm()
    
    def _setup_llm(self):
        """设置LLM模型"""
        print("[DEBUG] 开始设置LLM模型...")
        llm_config = self.config['models']['llm']
        provider = llm_config.get('provider', 'tongyi')
        print(f"[DEBUG] Provider: {provider}")
        print(f"[DEBUG] HAS_LANGCHAIN_TONGYI: {HAS_LANGCHAIN_TONGYI}")
        print(f"[DEBUG] HAS_LANGCHAIN_OPENAI: {HAS_LANGCHAIN_OPENAI}")
        
        if provider == 'tongyi':
            # 优先尝试使用Tongyi
            if HAS_LANGCHAIN_TONGYI:
                try:
                    from langchain_community.llms import Tongyi
                    api_key = llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
                    if not api_key:
                        raise ValueError("通义千问API密钥未设置，请在config.yaml中设置api_key或设置DASHSCOPE_API_KEY环境变量")
                    
                    # 设置环境变量（Tongyi在调用时需要DASHSCOPE_API_KEY环境变量）
                    os.environ['DASHSCOPE_API_KEY'] = api_key
                    print(f"[DEBUG] 已设置DASHSCOPE_API_KEY环境变量: {_mask_key(api_key)}")
                    
                    # 验证环境变量
                    env_check = os.getenv('DASHSCOPE_API_KEY')
                    if env_check != api_key:
                        print(f"[WARNING] 环境变量设置可能失败: {_mask_key(env_check)}")
                    
                    self.llm = Tongyi(
                        model_name=llm_config.get('model_name', 'qwen-turbo'),
                        dashscope_api_key=api_key,  # 显式传递
                        temperature=0.1
                    )
                    print("[OK] 使用通义千问模型")
                    
                    # 测试调用以确保环境变量正确
                    try:
                        test_response = self.llm.invoke("测试")
                        print("[OK] Tongyi模型测试调用成功")
                        # Tongyi成功，直接返回
                        return
                    except Exception as test_e:
                        print(f"[WARNING] Tongyi测试调用失败: {test_e}")
                        print("[INFO] 将回退到OpenAI兼容接口...")
                        raise  # 抛出错误以触发回退
                except Exception as e:
                    print(f"[ERROR] Tongyi初始化失败: {e}")
                    print("[INFO] 回退到OpenAI兼容接口...")
                    # 如果Tongyi失败，继续执行下面的OpenAI兼容接口代码
                    pass
            
            # 如果Tongyi不可用或失败，使用OpenAI兼容接口
            if HAS_LANGCHAIN_OPENAI:
                # 如果Tongyi不可用，使用OpenAI兼容接口（通义千问支持OpenAI兼容）
                print("[INFO] 使用OpenAI兼容接口连接通义千问")
                from langchain_openai import ChatOpenAI
                api_key = llm_config.get('api_key') or os.getenv('DASHSCOPE_API_KEY')
                api_base = llm_config.get('api_base', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
                
                if not api_key:
                    raise ValueError("通义千问API密钥未设置")
                
                print(f"[DEBUG] API Key: {_mask_key(api_key)} (长度: {len(api_key)})")
                print(f"[DEBUG] API Base: {api_base}")
                
                # 使用环境变量方式（最可靠，已验证可用）
                print("[DEBUG] 设置环境变量...")
                os.environ['OPENAI_API_KEY'] = api_key
                os.environ['OPENAI_API_BASE'] = api_base
                
                # 验证环境变量是否设置成功
                env_key = os.getenv('OPENAI_API_KEY')
                env_base = os.getenv('OPENAI_API_BASE')
                print(f"[DEBUG] 环境变量验证:")
                print(f"  OPENAI_API_KEY = {_mask_key(env_key)}")
                print(f"  OPENAI_API_BASE = {env_base}")
                
                # 直接使用环境变量初始化（已验证可用）
                print("[DEBUG] 初始化ChatOpenAI...")
                try:
                    self.llm = ChatOpenAI(
                        model=llm_config.get('model_name', 'qwen-turbo'),
                        temperature=0.1
                    )
                    print(f"[OK] ChatOpenAI初始化成功")
                    print(f"[DEBUG] LLM对象: {type(self.llm)}")
                    if hasattr(self.llm, 'openai_api_key'):
                        print(f"[DEBUG] LLM的API Key: {_mask_key(str(self.llm.openai_api_key))}")
                    if hasattr(self.llm, 'openai_api_base'):
                        print(f"[DEBUG] LLM的API Base: {self.llm.openai_api_base}")
                    print(f"[OK] 使用OpenAI兼容接口连接通义千问 (base_url: {api_base})")
                except Exception as e:
                    print(f"[ERROR] ChatOpenAI初始化失败: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            else:
                # 如果既没有Tongyi也没有OpenAI兼容接口
                raise ImportError(
                    "需要安装langchain相关包:\n"
                    "  pip install langchain-openai langchain-community"
                )
        else:
            # 使用OpenAI或其他模型
            if not HAS_LANGCHAIN_OPENAI:
                raise ImportError(
                    "需要安装langchain-openai:\n"
                    "  pip install langchain-openai"
                )
            
            from langchain_openai import ChatOpenAI
            api_key = llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API密钥未设置")
            
            # 使用OpenAI模型 - 直接使用环境变量（最可靠）
            os.environ['OPENAI_API_KEY'] = api_key
            self.llm = ChatOpenAI(
                model=llm_config.get('model_name', 'gpt-3.5-turbo'),
                temperature=0.1
            )
            print("[OK] 使用OpenAI模型")
    
    def query(self, question: str) -> Dict[str, Any]:
        """使用RAG回答问题"""
        if self.retriever is None:
            return {
                'answer': '检索器未初始化',
                'sources': []
            }
        
        # 检索相关文档
        result = self.retriever.retrieve(question)
        sources = result.get('sources', [])
        
        # 构建上下文
        context_parts = []
        for i, source in enumerate(sources[:3], 1):
            doc_name = source.get('metadata', {}).get('file_name', '未知文档')
            text = source.get('text', '')
            context_parts.append(f"[来源{i}: {doc_name}]\n{text}")
        
        context = "\n\n".join(context_parts)
        
        # 构建提示词
        prompt = f"""你是一个专业的财务助手，请基于以下文档内容回答用户问题。

文档内容：
{context}

用户问题：{question}

要求：
1. 用中文回答
2. 回答要准确、专业
3. 在回答中明确引用文档来源（格式：根据[来源X: 文档名]...）
4. 如果文档中没有相关信息，请说明

回答："""
        
        # 生成回答
        try:
            if hasattr(self.llm, 'invoke'):
                # 使用invoke方法（新版本LangChain）
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            elif hasattr(self.llm, '__call__'):
                # 使用call方法（旧版本）
                answer = self.llm(prompt)
            else:
                # 直接调用
                answer = str(self.llm(prompt))
        except Exception as e:
            error_msg = str(e)
            if 'API key' in error_msg or 'api_key' in error_msg.lower():
                answer = f"API密钥错误：{error_msg}\n请检查config.yaml中的api_key配置"
            else:
                answer = f"生成回答时出错：{error_msg}"
            print(f"[ERROR] LLM调用失败: {e}")
        
        return {
            'answer': answer,
            'sources': sources
        }

