# log sanitizer用于防止保护日志，防止日志被污染（injection attacks）

import re
from typing import Any, Optional

def sanitize_log_input(value: Any, max_length: int = 500) -> str:
    """
    处理用户控制的输入以进行安全日志记录。
    将危险字符（换行符、制表符、回车符等）替换为它们的转义表示（escaped representations），以防止日志注入攻击。
    这里转义表示就是将一些转义符号变成可见的，比如换行是 \n，在日志里会换行而不是显示\n字符。
    因此把它变成\\n，这样日志里就能看到\\n字符，而不是人类不可见的换行符（\n）。

    Args
        value: 要处理的输入值（Any 类型）
        max_length: 输出的最大长度，超过会截断

    Return:
        str: 清理后能被安全记录的字符串（日志）

    """
    if value is None:
        return "None"

    # Convert to string
    string_value = str(value)

    # 将一些危险的字符替换为它们的转义表示
    # 顺序很重要：首先转义反斜杠以避免双重转义。如果先替换\n 为 \\n, 再定义替换 \\ 为 \\\\
    # 那么之前被转义过的其它字符（如\\n）会被再次转义，成为\\\\n，导致日志里出现多余的反斜杠
    replacements = {
        "\\": "\\\\",  # Backslash (must be first)
        "\n": "\\n",   # Newline - prevents creating new log entries
        "\r": "\\r",   # Carriage return
        "\t": "\\t",   # Tab
        "\x00": "\\0",  # Null character
        "\x1b": "\\x1b",  # Escape character (used in ANSI sequences)
    }

    for char, replacement in replacements.items():
        string_value = string_value.replace(char, replacement)

    # 删除其他不常用的控制字符（ASCII 0-31，除了那些已经处理过的字符）
    # 这些在日志中很少有用，并且可能被利用于进行注入攻击
    string_value = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", string_value)

    # 如果超过定义长度就截断（防止日志泛滥）
    if len(string_value) > max_length:
        string_value = string_value[: max_length - 3] + "..."

    return string_value

# 下面大多数函数都是调用了sanitize_log_input，只是用于不同场景，并且根据场景不同传入了不同的value和max_length

def sanitize_thread_id(thread_id: Any) -> str:
    """
    处理用于记录的 thread_id.

    tread id应该是带有 连字符 和 下划线 的字母数字，但我们进行了处理以进行防御。

    Args:
        thread_id: 要处理的thread ID

    Returns:
        str: 处理后的 thread ID
    """
    return sanitize_log_input(thread_id, max_length=100)

def sanitize_user_content(content: Any) -> str:
    """
    Sanitize user-provided message content for logging.

    User messages can be arbitrary length, so we truncate more aggressively.

    Args:
        content: The user content to sanitize

    Returns:
        str: Sanitized user content
    """
    return sanitize_log_input(content, max_length=200)


def sanitize_agent_name(agent_name: Any) -> str:
    """
    Sanitize agent name for logging.

    Agent names should be simple identifiers, but we sanitize to be defensive.

    Args:
        agent_name: The agent name to sanitize

    Returns:
        str: Sanitized agent name
    """
    return sanitize_log_input(agent_name, max_length=100)


def sanitize_tool_name(tool_name: Any) -> str:
    """
    Sanitize tool name for logging.

    Tool names should be simple identifiers, but we sanitize to be defensive.

    Args:
        tool_name: The tool name to sanitize

    Returns:
        str: Sanitized tool name
    """
    return sanitize_log_input(tool_name, max_length=100)


def sanitize_feedback(feedback: Any) -> str:
    """
    Sanitize user feedback for logging.

    Feedback can be arbitrary text from interrupts, so sanitize carefully.

    Args:
        feedback: The feedback to sanitize

    Returns:
        str: Sanitized feedback (truncated more aggressively)
    """
    return sanitize_log_input(feedback, max_length=150)


def create_safe_log_message(template: str, **kwargs) -> str:
    """
    Create a safe log message by sanitizing all values.

    Uses a template string with keyword arguments, sanitizing each value
    before substitution to prevent log injection.

    Args:
        template: Template string with {key} placeholders
        **kwargs: Key-value pairs to substitute

    Returns:
        str: Safe log message

    Example:
        >>> msg = create_safe_log_message(
        ...     "[{thread_id}] Processing {tool_name}",
        ...     thread_id="abc\\n[INFO]",
        ...     tool_name="my_tool"
        ... )
        >>> "[abc\\\\n[INFO]] Processing my_tool" in msg
        True
    """
    # Sanitize all values
    safe_kwargs = {
        key: sanitize_log_input(value) for key, value in kwargs.items()
    }

    # Substitute into template
    return template.format(**safe_kwargs)
