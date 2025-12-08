# 用于在LLM调用工具前先中断，等待用户进行确认或者其它的处理
import json
import logging
from typing import Any, Callable, List, Optional

from langchain_core.tools import BaseTool
from langgraph.types import interrupt

# 导入用于清理写入日志内容的函数，防止injection attack
from src.utils.log_sanitizer import (
    sanitize_feedback,
    sanitize_log_input,
    sanitize_tool_name,
)

logger = logging.getLogger(__name__)

class ToolInterceptor:
    """Intercepts tool calls and triggers interrupts for specified tools."""

    def __init__(self, interrupt_before_tools: Optional[List[str]] = None):
        """先初始化需要中断的工具（工具名字包含在列表 interrupt_before_tools）

        Args:
            interrupt_before_tools: 执行前要中断的工具名称列表.
                                    If None or empty, no interrupts are triggered.
        """
        self.interrupt_before_tools = interrupt_before_tools or []
        logger.info(
            f"ToolInterceptor initialized with interrupt_before_tools: {self.interrupt_before_tools}"
        )

    def should_interrupt(self, tool_name: str) -> bool:
        """检查目前即将调用的工具名称是否在需要中断的工具列表中

        Args:
            tool_name: 即将被调用的工具名称

        Returns:
            bool: 如果工具应该触发中断，则为True，否则为False
        """
        should_interrupt = tool_name in self.interrupt_before_tools
        if should_interrupt:
            logger.info(f"Tool '{tool_name}' marked for interrupt")
        return should_interrupt

    @staticmethod
    def _format_tool_input(tool_input: Any) -> str:
        """格式化工具输入以便在中断消息中显示。

        尝试格式化为JSON以获得更好的可读性，并退回到字符串表示。

        Args:
            tool_input: The tool input to format

        Returns:
            str: Formatted representation of the tool input
        """
        if tool_input is None:
            return "No input"

        # 为了更好的可读性，尝试先序列化为JSON
        try:
            # 如果是 dict, list, tuple 直接序列化
            if isinstance(tool_input, (dict, list, tuple)):
                return json.dumps(tool_input, indent=2, default=str)
            # 如果是字符串，直接返回
            elif isinstance(tool_input, str):
                return tool_input
            else:
                # 对于其他类型，如果它具有__dict__，则尝试转换为dict
                # 否则退回到字符串表示
                return str(tool_input)
        except (TypeError, ValueError):
            # JSON序列化失败，使用字符串表示
            return str(tool_input)

    @staticmethod
    def wrap_tool(
        tool: BaseTool, interceptor: "ToolInterceptor"
    ) -> BaseTool:
        """通过创建wrapper来包装一个工具，以添加中断逻辑。

        Args:
            tool: 要包装的工具
            interceptor: ToolInterceptor实例

        Returns:
            BaseTool: 具有中断功能的封装工具
        """

        # 先拿到工具的function和名字
        original_func = tool.func
        safe_tool_name = sanitize_tool_name(tool.name)
        logger.debug(f"Wrapping tool '{safe_tool_name}' with interrupt capability")

        def intercepted_func(*args: Any, **kwargs: Any) -> Any:
            """对工具做一些处理和检查
            包括：
                对工具的名字，输入等做处理然后写入日志
                检查是否需要中断
            """
            tool_name = tool.name
            safe_tool_name_local = sanitize_tool_name(tool_name)
            logger.debug(f"[ToolInterceptor] Executing tool: {safe_tool_name_local}")
            
            # Format tool input for display
            tool_input = args[0] if args else kwargs
            tool_input_repr = ToolInterceptor._format_tool_input(tool_input)
            safe_tool_input = sanitize_log_input(tool_input_repr, max_length=100)
            logger.debug(f"[ToolInterceptor] Tool input: {safe_tool_input}")

            should_interrupt = interceptor.should_interrupt(tool_name)
            logger.debug(f"[ToolInterceptor] should_interrupt={should_interrupt} for tool '{safe_tool_name_local}'")
            
            # 如果需要 中断
            if should_interrupt:
                logger.info(
                    f"[ToolInterceptor] Interrupting before tool '{safe_tool_name_local}'"
                )
                logger.debug(
                    f"[ToolInterceptor] Interrupt message: About to execute tool '{safe_tool_name_local}' with input: {safe_tool_input}..."
                )
                
                # 触发中断并等待用户反馈
                try:
                    feedback = interrupt(
                        f"About to execute tool: '{tool_name}'\n\nInput:\n{tool_input_repr}\n\nApprove execution?"
                    ) # 用户反馈   
                    safe_feedback = sanitize_feedback(feedback)
                    logger.debug(f"[ToolInterceptor] Interrupt returned with feedback: {f'{safe_feedback[:100]}...' if safe_feedback and len(safe_feedback) > 100 else safe_feedback if safe_feedback else 'None'}")
                except Exception as e:
                    logger.error(f"[ToolInterceptor] Error during interrupt: {str(e)}")
                    raise

                logger.debug(f"[ToolInterceptor] Processing feedback approval for '{safe_tool_name_local}'")
                
                # 使用下面定义的_parse_approval来解析用户的反馈 feedback， 
                # _parse_approval定义了一些关键词以匹配常见的同意词汇（yes，approve等）会返回一个布尔值
                is_approved = ToolInterceptor._parse_approval(feedback)
                logger.info(f"[ToolInterceptor] Tool '{safe_tool_name_local}' approval decision: {is_approved}")
                # 如果不同意，直接return，此时工具处于中断状态，因此等于没有被执行
                if not is_approved:
                    logger.warning(f"[ToolInterceptor] User rejected execution of tool '{safe_tool_name_local}'")
                    return {
                        "error": f"Tool execution rejected by user",
                        "tool": tool_name,
                        "status": "rejected",
                    }

                logger.info(f"[ToolInterceptor] User approved execution of tool '{safe_tool_name_local}', proceeding")

            # 如果没有不同意，那么会执行到这一步
            # 执行原始工具
            try:
                logger.debug(f"[ToolInterceptor] Calling original function for tool '{safe_tool_name_local}'")
                result = original_func(*args, **kwargs)
                logger.info(f"[ToolInterceptor] Tool '{safe_tool_name_local}' execution completed successfully")
                result_len = len(str(result))
                logger.debug(f"[ToolInterceptor] Tool result length: {result_len}")
                return result
            except Exception as e:
                logger.error(f"[ToolInterceptor] Error executing tool '{safe_tool_name_local}': {str(e)}")
                raise

        # 执行中断和一系列检查、确认
        # 使用object.__setattr__绕过Pydantic验证
        logger.debug(f"Attaching intercepted function to tool '{safe_tool_name}'")
        object.__setattr__(tool, "func", intercepted_func)
        return tool

    @staticmethod
    def _parse_approval(feedback: str) -> bool:
        """解析用户反馈以确定是否批准了工具的执行。

        Args:
            feedback: 来自用户的反馈字符串

        Returns:
            bool: True if feedback indicates approval, False otherwise
        """
        if not feedback:
            logger.warning("Empty feedback received, treating as rejection")
            return False

        feedback_lower = feedback.lower().strip()

        # 定义的一些关于 “同意” 的关键词
        approval_keywords = [
            "approved",
            "approve",
            "yes",
            "proceed",
            "continue",
            "ok",
            "okay",
            "accepted",
            "accept",
            "[approved]",
        ]
        # 如果同意就返回True
        for keyword in approval_keywords:
            if keyword in feedback_lower:
                return True

        # Default to rejection if no approval keywords found
        logger.warning(
            f"No approval keywords found in feedback: {feedback}. Treating as rejection."
        )
        return False


def wrap_tools_with_interceptor(
    tools: List[BaseTool], interrupt_before_tools: Optional[List[str]] = None
) -> List[BaseTool]:
    """这个函数用于包装一组工具，使其在调用前可以中断以进行用户确认。

    1. 先检查有没有定义需要中断的工具，没定义就直接返回。
    2. 如果有定义，就实例化一个 ToolInterceptor。
    3. 遍历传入的工具列表，使用 ToolInterceptor 的 wrap_tool 方法开始包装：
        检查是否需要包装，需要则包装，不需要则跳过

    Args:
        tools: 要被包装的工具列表
        interrupt_before_tools: 定义的需要中断以进行确认的工具列表

    Returns:
        List[BaseTool]: 被包装后的工具列表
    """

    # 1. 先检查有没有定义需要中断的工具
    if not interrupt_before_tools:
        logger.debug("No tool interrupts configured, returning tools as-is")
        return tools

    logger.info(
        f"Wrapping {len(tools)} tools with interrupt logic for: {interrupt_before_tools}"
    )
    # 2. 实例化一个 ToolInterceptor
    interceptor = ToolInterceptor(interrupt_before_tools)

    wrapped_tools = []
    # 3. 遍历传入的工具列表，开始检查和包装 需要包装的工具
    for tool in tools:
        try:
            wrapped_tool = ToolInterceptor.wrap_tool(tool, interceptor)
            wrapped_tools.append(wrapped_tool)
            logger.debug(f"Wrapped tool: {tool.name}")
        except Exception as e:
            logger.error(f"Failed to wrap tool {tool.name}: {str(e)}")
            # Add original tool if wrapping fails
            wrapped_tools.append(tool)

    logger.info(f"Successfully wrapped {len(wrapped_tools)} tools")
    return wrapped_tools