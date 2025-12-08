import logging
from typing import List, Optional

from langgraph.prebuilt import create_react_agent

# 导入 工具拦截器，在即将执行工具时中断，等待用户确认是否继续执行
from .tool_interceptor import wrap_tools_with_interceptor

from src.config.agents import AGENT_LLM_MAP
from src.llms.llm import get_llm_by_type
from src.prompts import apply_prompt_template

logger = logging.getLogger(__name__)

# 使用配置的 LLM type 创建代理
def create_agent(
    agent_name: str,
    agent_type: str,
    tools: list,
    prompt_template: str,
    pre_model_hook: callable = None,
    interrupt_before_tools: Optional[List[str]] = None,
):
    """
    在LangGraph create_react_agent基础上封装一个创建Agent的函数，从而能够添加一些定制化功能：
    例如：工具执行前中断确认功能；根据agent_type选择不同的LLM类型等。
    

    Args:
        agent_name: agent的名字（自己取）
        agent_type: agent的类型（用于映射LLM类型），跟 src\config\AGENT_LLM_MAP 中的key对应
        tools: agent可用的工具列表 （取决于自己定了哪些工具）
        prompt_template: 要使用的提示模板的名称 （根据 src\prompts\ 中的md文件）
        pre_model_hook: 可选的hook，用于在模型调用之前预处理状态
        interrupt_before_tools: 需要在执行前中断的工具名单（可选，自定义）

    Returns:
        配置好的agent graph
    """
    logger.debug(
        f"Creating agent '{agent_name}' of type '{agent_type}' "
        f"with {len(tools)} tools and template '{prompt_template}'"
    )
    
    # 创建processed_tools用于存储 包装后的 有中断逻辑的工具列表（如果需要中断）
    # 不需要中断则直接使用 processed_tools
    processed_tools = tools

    # 如果配置了需要中断确认的工具，则进行包装，加入中断逻辑
    if interrupt_before_tools:
        logger.info(
            f"Creating agent '{agent_name}' with tool-specific interrupts: {interrupt_before_tools}"
        )
        logger.debug(f"Wrapping {len(tools)} tools for agent '{agent_name}'")
        processed_tools = wrap_tools_with_interceptor(tools, interrupt_before_tools)
        logger.debug(f"Agent '{agent_name}' tool wrapping completed")
    else:
        logger.debug(f"Agent '{agent_name}' has no interrupt-before-tools configured")

    if agent_type not in AGENT_LLM_MAP:
        logger.warning(
            f"Agent type '{agent_type}' not found in AGENT_LLM_MAP. "
            f"Falling back to default LLM type 'basic' for agent '{agent_name}'. "
            "This may indicate a configuration issue."
        )
    # 根据agent 类型获取对应的LLM类型，默认使用 "basic"
    llm_type = AGENT_LLM_MAP.get(agent_type, "basic")
    logger.debug(f"Agent '{agent_name}' using LLM type: {llm_type}")
    
    logger.debug(f"Creating ReAct agent '{agent_name}'")
    # 只用LangGraph创建agent，传入包装后的加入了中断逻辑工具列表（如需中断），不需要中断则传入的是没有中断逻辑工具列表  
    agent = create_react_agent(
        name=agent_name,
        model=get_llm_by_type(llm_type),
        tools=processed_tools,
        prompt=lambda state: apply_prompt_template(
            prompt_template, state, locale=state.get("locale", "en-US")
        ),
        pre_model_hook=pre_model_hook,
    )
    logger.info(f"Agent '{agent_name}' created successfully")
    
    return agent