"""
基于LangChain的BaseTools实现的工具，能够调用InfoQuest Search API进行网络搜索。
简单说，这里实例化了 InfoQuestAPIWrapper 类，可以进行搜索和结果清洗
最终返回清洗后的结果

额外一些功能的定义
    输入的Pydantic模型
    工具元信息
    搜索参数的设置（匹配 InfoQuestAPIWrapper 的参数），例如时间范围过滤、站点过滤等
"""

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.infoquest_search.infoquest_search_api import InfoQuestAPIWrapper

logger = logging.getLogger(__name__)


class InfoQuestInput(BaseModel):
    """
    定义输入模型

    Attributes:
        query (str): 搜索查询字符串，用户想要搜索的内容
    """

    query: str = Field(description="search query to look up")

class InfoQuestSearchResults(BaseTool):
    """
    用于调用 InfoQuest搜索工具，并且返回清洗后且结构化的结果（文字/图片）

    配置说明:
        需要安装依赖包并设置环境变量 ``INFOQUEST_API_KEY``。

        .. code-block:: bash

            pip install -U langchain-community aiohttp
            export INFOQUEST_API_KEY="your-api-key"

    实例化示例:
        .. code-block:: python

            from your_module import InfoQuestSearch 

            tool = InfoQuestSearchResults(
                output_format="json",
                time_range=10,          # 只返回最近10天的结果
                site="nytimes.com"      # 只搜索纽约时报
            )

    直接调用示例:
        .. code-block:: python

            tool.invoke({
                'query': 'who won the last french open'
            })

        返回结果格式:
        .. code-block:: json

            [
                {
                    "type": "page",
                    "title": "Djokovic Claims French Open Title...",
                    "url": "https://www.nytimes.com/...",
                    "desc": "Novak Djokovic won the 2024 French Open by defeating Casper Ruud..."
                },
                {
                    "type": "news",
                    "time_frame": "2 days ago",
                    "title": "French Open Finals Recap",
                    "url": "https://www.nytimes.com/...",
                    "source": "New York Times"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://www.nytimes.com/.../djokovic.jpg"},
                    "image_description": "Novak Djokovic celebrating his French Open victory"
                }
            ]

    作为工具调用示例 (Agent 调用方式):
        .. code-block:: python

            tool.invoke({
                "args": {
                    'query': 'who won the last french open',
                },
                "type": "tool_call",
                "id": "foo",
                "name": "infoquest"
            })

        返回 ToolMessage 对象，content 字段包含 JSON 格式的搜索结果。
    """  # noqa: E501

    # ==================== 工具元信息 ====================
    name: str = "infoquest_search_results_json"
    """工具名称，Agent 通过此名称识别和调用工具"""

    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    """工具描述，Agent 根据此描述决定何时使用该工具"""

    args_schema: Type[BaseModel] = InfoQuestInput
    """输入参数的 Pydantic 模型，定义工具接受的参数结构"""

    # ==================== 搜索配置参数 ====================
    time_range: int = -1
    """
    搜索结果的时间范围过滤（单位：天）。
    
    - 正整数（如 30）：只返回最近 N 天内的结果
    - -1（默认）：不进行时间过滤
    """

    site: str = ""
    """
    站点过滤，限制搜索结果来源于特定域名（如 "nytimes.com"）。
    
    - 非空字符串：只返回该域名的结果
    - 空字符串（默认）：不限制域名
    """

    # ==================== 内部组件 ====================
    api_wrapper: InfoQuestAPIWrapper = Field(default_factory=InfoQuestAPIWrapper)  # type: ignore[arg-type]
    """API 封装器实例，负责实际的 HTTP 请求"""

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    """响应格式，content_and_artifact 表示返回内容和原始数据的元组"""

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化 InfoQuest 搜索工具。

        如果提供了 infoquest_api_key 参数，会用它创建 API 封装器；
        否则会尝试从环境变量 INFOQUEST_API_KEY 获取。

        Args:
            **kwargs: 关键字参数，可包含：
                - infoquest_api_key (str): API 密钥（可选，也可通过环境变量设置）
                - time_range (int): 时间范围过滤，单位为天
                - site (str): 站点过滤
                - 其他 BaseTool 支持的参数

        Returns:
            None
        """
        # 如果显式传入了 API 密钥，则用它创建 api_wrapper
        if "infoquest_api_key" in kwargs:
            kwargs["api_wrapper"] = InfoQuestAPIWrapper(
                infoquest_api_key=kwargs["infoquest_api_key"]
            )
            logger.debug("API wrapper initialized with provided key")

        # 调用父类构造函数
        super().__init__(**kwargs)

        # 打印初始化信息（便于调试和确认配置）
        logger.info(
            "\n============================================\n"
            "🚀 BytePlus InfoQuest Search Initialization 🚀\n"
            "============================================"
        )
        
        # 准备初始化详情的日志输出
        time_range_status = f"{self.time_range} days" if hasattr(self, 'time_range') and self.time_range > 0 else "Disabled"
        site_filter = f"'{self.site}'" if hasattr(self, 'site') and self.site else "Disabled"
        
        initialization_details = (
            f"\n🔧 Tool Information:\n"
            f"├── Tool Name: {self.name}\n"
            f"├── Time Range Filter: {time_range_status}\n"
            f"└── Site Filter: {site_filter}\n"
            f"📊 Configuration Summary:\n"
            f"├── Response Format: {self.response_format}\n"
        )
        
        logger.info(initialization_details)
        logger.info("\n" + "*" * 70 + "\n")

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        """
        同步执行搜索（LangChain BaseTool 要求实现的核心方法）。

        该方法会：
        1. 通过infoquest_search_api.py的 InfoQuestAPIWrapper调用 InfoQuest API 获取原始搜索结果
        2. 清洗和格式化结果
        3. 返回 JSON 字符串和原始数据

        Args:
            query (str): 搜索查询字符串
            run_manager (Optional[CallbackManagerForToolRun]): 
                LangChain 回调管理器，用于追踪工具执行过程（可选）

        Returns:
            Tuple[Union[List[Dict[str, str]], str], Dict]: 返回一个元组：
                - 第一个元素：JSON 格式的搜索结果字符串，包含清洗后的结果列表；
                  如果出错则返回包含 error 字段的 JSON
                - 第二个元素：原始 API 响应数据字典；如果出错则为空字典
        """
        try:
            logger.debug(f"Executing search with parameters: time_range={self.time_range}, site={self.site}")
            
            # 调用 API 获取原始结果 （infoquest_search_api.py的 InfoQuestAPIWrapper的方法）
            raw_results = self.api_wrapper.raw_results(
                query,
                self.time_range,
                self.site
            )
            
            # 清洗和格式化结果（infoquest_search_api.py的 InfoQuestAPIWrapper的方法）
            logger.debug("Processing raw search results")
            cleaned_results = self.api_wrapper.clean_results_with_images(raw_results["results"])

            # 转换为 JSON 字符串（ensure_ascii=False 保留中文等非 ASCII 字符）
            result_json = json.dumps(cleaned_results, ensure_ascii=False)

            logger.info(
                f"Search tool execution completed | "
                f"mode=synchronous | "
                f"results_count={len(cleaned_results)}"
            )
            return result_json, raw_results
        except Exception as e:
            # 捕获异常并返回错误信息
            logger.error(
                f"Search tool execution failed | "
                f"mode=synchronous | "
                f"error={str(e)}"
            )
            error_result = json.dumps({"error": repr(e)}, ensure_ascii=False)
            return error_result, {}

    async def _arun(
            self,
            query: str,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        """
        异步执行搜索（LangChain BaseTool 的异步版本核心方法）。

        与 _run 方法功能相同，但使用异步方式调用 API。
        适用于需要并发处理多个搜索请求的场景，可提高整体吞吐量。

        Args:
            query (str): 搜索查询字符串
            run_manager (Optional[AsyncCallbackManagerForToolRun]): 
                LangChain 异步回调管理器，用于追踪工具执行过程（可选）

        Returns:
            Tuple[Union[List[Dict[str, str]], str], Dict]: 返回一个元组：
                - 第一个元素：JSON 格式的搜索结果字符串，包含清洗后的结果列表；
                  如果出错则返回包含 error 字段的 JSON
                - 第二个元素：原始 API 响应数据字典；如果出错则为空字典
        """
        # 记录请求开始日志（截断过长的查询以保护日志可读性）
        if logger.isEnabledFor(logging.DEBUG):
            query_truncated = query[:50] + "..." if len(query) > 50 else query
            logger.debug(
                f"Search tool execution started | "
                f"mode=asynchronous | "
                f"query={query_truncated}"
            )
        try:
            logger.debug(f"Executing async search with parameters: time_range={self.time_range}, site={self.site}")

            # 异步调用 API 获取原始结果
            raw_results = await self.api_wrapper.raw_results_async(
                query,
                self.time_range,
                self.site
            )

            # 清洗和格式化结果（注意：clean_results_with_images 是同步方法）
            logger.debug("Processing raw async search results")
            cleaned_results = self.api_wrapper.clean_results_with_images(raw_results["results"])

            # 转换为 JSON 字符串
            result_json = json.dumps(cleaned_results, ensure_ascii=False)

            logger.debug(
                f"Search tool execution completed | "
                f"mode=asynchronous | "
                f"results_count={len(cleaned_results)}"
            )

            return result_json, raw_results
        except Exception as e:
            # 捕获异常并返回错误信息
            logger.error(
                f"Search tool execution failed | "
                f"mode=asynchronous | "
                f"error={str(e)}"
            )
            error_result = json.dumps({"error": repr(e)}, ensure_ascii=False)
            return error_result, {}