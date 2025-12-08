"""
为工具添加日志功能
可以 调试和监控工具；追踪工具执行链

例如：
LoggedTavilySearch = create_logged_tool(TavilySearchWithImages)
创建具有日志功能的TavilySearchWithImages工具
这里是有个多继承。工具（TavilySearchWithImages）一般继承自 BaseTool类
然后 create_logged_tool其实是 class LoggedTool(LoggedToolMixin, TavilySearchWithImages)

也就是说最后的 LoggedTavilySearch 其实是 LoggedTavilySearch --- 继承自 --> LoggedToolMixin --继承自-> BaseTool
所以 LoggedTavilySearch 调用 _run 方法时，实际上会先调用 LoggedToolMixin 里的 _run 方法，然后再通过_run里写的super._run()调用 BaseTool 里的 _run 方法。
"""

import functools
import logging
from typing import Any, Callable, Type, TypeVar

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

# 泛型类型变量，用于factory function的类型提示
T = TypeVar("T")


def log_io(func: Callable) -> Callable:
    """
    记录工具函数输入参数和输出结果的装饰器。

    这个装饰器会在函数调用前后自动记录日志，包括：
    - 调用时的所有位置参数和关键字参数
    - 函数执行后的返回值

    Args:
        func: 要装饰的工具函数

    Returns:
        带有输入/输出日志记录功能的包装函数

    使用示例:
        @log_io
        def my_tool(param1, param2):
            return result
    """

    @functools.wraps(func)  # 保留原函数的元信息（如函数名、文档字符串等）
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取函数名称
        func_name = func.__name__
        # 将所有参数格式化为可读字符串
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        # 记录输入参数
        logger.info(f"Tool {func_name} called with parameters: {params}")

        # 执行原始函数
        result = func(*args, **kwargs)

        # 记录输出结果
        logger.info(f"Tool {func_name} returned: {result}")

        return result

    return wrapper


class LoggedToolMixin:
    """
    为工具类添加日志功能的 Mixin 类。

    通过多重继承的方式，可以为任何工具类添加自动日志记录功能。
    该 Mixin 会拦截工具的 _run 方法，在执行前后记录相关信息。

    使用方式：
        class MyLoggedTool(LoggedToolMixin, BaseTool):
            pass
    """

    def _log_operation(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """
        记录工具操作的辅助方法。

        Args:
            method_name: 被调用的方法名称
            *args: 位置参数
            **kwargs: 关键字参数
        """
        # 从类名中移除 "Logged" 前缀，获取原始工具名称
        tool_name = self.__class__.__name__.replace("Logged", "")
        # 格式化参数为可读字符串
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        logger.debug(f"Tool {tool_name}.{method_name} called with parameters: {params}")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        重写 _run 方法以添加日志记录功能。 这里的 _run方法是继承自 BaseTool类，这根日志功能的创建有关，看最上面

        该方法会：
        1. 在执行前记录输入参数
        2. 调用父类的 _run 方法执行实际操作
        3. 在执行后记录返回结果

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            父类 _run 方法的返回结果
        """
        # 记录调用信息
        self._log_operation("_run", *args, **kwargs)
        # 调用父类（即原始工具类）的 _run 方法
        result = super()._run(*args, **kwargs)
        # 记录返回结果
        logger.debug(
            f"Tool {self.__class__.__name__.replace('Logged', '')} returned: {result}"
        )
        return result


def create_logged_tool(base_tool_class: Type[T]) -> Type[T]:
    """
    factory function：为任意工具类创建带日志功能的版本。

    该函数通过动态创建新类的方式，将 LoggedToolMixin 的日志功能
    与原始工具类结合，生成一个新的带日志记录功能的工具类。

    Args:
        base_tool_class: 需要增强日志功能的原始工具类

    Returns:
        一个新的类，继承自 LoggedToolMixin 和原始工具类，
        具备自动日志记录功能

    使用示例:
        LoggedSearchTool = create_logged_tool(SearchTool)
        tool = LoggedSearchTool()
    """

    class LoggedTool(LoggedToolMixin, base_tool_class):
        """动态生成的带日志功能的工具类"""
        pass

    # 设置更具描述性的类名，方便调试和日志识别
    LoggedTool.__name__ = f"Logged{base_tool_class.__name__}"
    return LoggedTool