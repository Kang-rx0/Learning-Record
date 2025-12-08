"""
用于调用 InfoQuest Search API 的一些函数：
    从环境获取 Key
    根据query调用 API 获取原始结果（同步和异步） 
    清洗和结构化获得的结果（文字/图片）

要设置此功能，请遵循以下说明：:
https://docs.byteplus.com/en/docs/InfoQuest/What_is_Info_Quest
"""

import json
from typing import Any, Dict, List

import aiohttp
import requests
from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator
from src.config import load_yaml_config
import logging

logger = logging.getLogger(__name__)

# 搜索API的base URL
INFOQUEST_API_URL = "https://search.infoquest.bytepluses.com"

# 读取相关的配置
def get_search_config():
    """
    从配置文件中读取搜索引擎相关配置。

    Args:
        无

    Returns:
        dict: 搜索引擎配置字典，包含 API 密钥、默认参数等配置项。
              如果配置文件中没有 SEARCH_ENGINE 节，则返回空字典。
    """
    config = load_yaml_config("conf.yaml")
    search_config = config.get("SEARCH_ENGINE", {})
    return search_config

class InfoQuestAPIWrapper(BaseModel):
    """est搜索API的包装"""

    infoquest_api_key: SecretStr
    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Any:
        """
        验证环境中存在 API 密钥。

        这是 Pydantic 的模型验证器，在模型实例化之前执行。
        会尝试从传入的字典或环境变量中获取 API 密钥。

        Args:
            values (Dict): 传入的初始化参数字典

        Returns:
            Dict: 验证并补充后的参数字典，包含 infoquest_api_key
        """
        logger.info("Initializing BytePlus InfoQuest Product - Search API client")

        # 这里是从环境中读取 API Key
        infoquest_api_key = get_from_dict_or_env(
            values, "infoquest_api_key", "INFOQUEST_API_KEY"
        )
        values["infoquest_api_key"] = infoquest_api_key

        logger.info("BytePlus InfoQuest Product - Environment validation successful")
        return values

    def raw_results(
        self,
        query: str,
        time_range: int,
        site: str,
        output_format: str = "JSON",
    ) -> Dict:
        """
        同步调用 InfoQuest Search API 获取原始搜索结果。

        Args:
            query (str): 搜索查询字符串
            time_range (int): 时间范围过滤（天数）。0 表示不限制时间范围
            site (str): 站点过滤，限制搜索特定网站。空字符串表示不限制
            output_format (str): 输出格式，默认为 "JSON"

        Returns:
            Dict: API 返回的原始搜索结果字典，包含 organic（网页）、
                  top_stories（新闻）、images（图片）等搜索结果
        """
        if logger.isEnabledFor(logging.DEBUG):
            query_truncated = query[:50] + "..." if len(query) > 50 else query
            logger.debug(
                f"InfoQuest - Search API request initiated | "
                f"operation=search | "
                f"query_truncated={query_truncated} | "
                f"has_time_filter={time_range > 0} | "
                f"has_site_filter={bool(site)} | "
                f"request_type=sync"
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.infoquest_api_key.get_secret_value()}",
        }

        params = {
            "format": output_format,
            "query": query
        }
        if time_range > 0:
            params["time_range"] = time_range
            logger.debug(f"InfoQuest - Applying time range filter: time_range_days={time_range}")

        if site != "":
            params["site"] = site
            logger.debug(f"InfoQuest - Applying site filter: site={site}")

        response = requests.post(
            f"{INFOQUEST_API_URL}",
            headers=headers,
            json=params
        )
        response.raise_for_status()

        # 打印部分响应以便调试
        response_json = response.json()
        if logger.isEnabledFor(logging.DEBUG):
            response_sample = json.dumps(response_json)[:200] + ("..." if len(json.dumps(response_json)) > 200 else "")
            logger.debug(
                f"Search API request completed successfully | "
                f"service=InfoQuest | "
                f"status=success | "
                f"response_sample={response_sample}"
            )

        return response_json["search_result"]

    async def raw_results_async(
        self,
        query: str,
        time_range: int,
        site: str,
        output_format: str = "JSON",
    ) -> Dict:
        """
        异步调用 InfoQuest Search API 获取原始搜索结果。

        与 raw_results 功能相同，但使用 aiohttp 进行异步 HTTP 请求，
        适用于需要并发处理多个搜索请求的场景。

        Args:
            query (str): 搜索查询字符串
            time_range (int): 时间范围过滤（天数）。0 表示不限制时间范围
            site (str): 站点过滤，限制搜索特定网站。空字符串表示不限制
            output_format (str): 输出格式，默认为 "JSON"

        Returns:
            Dict: API 返回的原始搜索结果字典，包含 organic（网页）、
                  top_stories（新闻）、images（图片）等搜索结果

        Raises:
            Exception: 当 API 请求失败时抛出异常，包含状态码和错误原因
        """

        if logger.isEnabledFor(logging.DEBUG):
            query_truncated = query[:50] + "..." if len(query) > 50 else query
            logger.debug(
                f"BytePlus InfoQuest - Search API async request initiated | "
                f"operation=search | "
                f"query_truncated={query_truncated} | "
                f"has_time_filter={time_range > 0} | "
                f"has_site_filter={bool(site)} | "
                f"request_type=async"
            )
        # 函数来执行API调用
        async def fetch() -> str:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.infoquest_api_key.get_secret_value()}",
            }
            params = {
                "format": output_format,
                "query": query,
            }
            if time_range > 0:
                params["time_range"] = time_range
                logger.debug(f"Applying time range filter in async request: {time_range} days")
            if site != "":
                params["site"] = site
                logger.debug(f"Applying site filter in async request: {site}")

            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.post(f"{INFOQUEST_API_URL}", headers=headers, json=params) as res:
                    if res.status == 200:
                        data = await res.text()
                        return data
                    else:
                        raise Exception(f"Error {res.status}: {res.reason}")
        results_json_str = await fetch()

        # Print partial response for debugging
        if logger.isEnabledFor(logging.DEBUG):
            response_sample = results_json_str[:200] + ("..." if len(results_json_str) > 200 else "")
            logger.debug(
                f"Async search API request completed successfully | "
                f"service=InfoQuest | "
                f"status=success | "
                f"response_sample={response_sample}"
            )
        return json.loads(results_json_str)["search_result"]

    def clean_results_with_images(
        self, raw_results: List[Dict[str, Dict[str, Dict[str, Any]]]]
    ) -> List[Dict]:
        """
        清洗和格式化 InfoQuest Search API 的原始搜索结果。

        该方法会：
        1. 提取网页（organic）、新闻（top_stories）、图片（images）三类结果
        2. 去除重复的 URL
        3. 统一格式化为标准的结果字典

        Args:
            raw_results (List[Dict]): API 返回的原始搜索结果列表，
                每个元素包含 content -> results 的嵌套结构

        Returns:
            List[Dict]: 清洗后的搜索结果列表，每个元素为以下格式之一：
                - 网页: {"type": "page", "title": str, "url": str, "desc": str}
                - 新闻: {"type": "news", "time_frame": str, "title": str, 
                         "url": str, "source": str}
                - 图片: {"type": "image_url", "image_url": str, 
                         "image_description": str}
        """
        logger.debug("Processing search results")

        seen_urls = set()
        clean_results = []
        counts = {"pages": 0, "news": 0, "images": 0}

        for content_list in raw_results:
            content = content_list["content"]
            results = content["results"]


            if results.get("organic"):
                organic_results = results["organic"]
                for result in organic_results:
                    clean_result = {
                        "type": "page",
                        "title": result["title"],
                        "url": result["url"],
                        "desc": result["desc"],
                    }
                    url = clean_result["url"]
                    if isinstance(url, str) and url and url not in seen_urls:
                        seen_urls.add(url)
                        clean_results.append(clean_result)
                        counts["pages"] += 1

            if results.get("top_stories"):
                news = results["top_stories"]
                for obj in news["items"]:
                    clean_result = {
                        "type": "news",
                        "time_frame": obj["time_frame"],
                        "title": obj["title"],
                        "url": obj["url"],
                        "source": obj["source"],
                    }
                    url = clean_result["url"]
                    if isinstance(url, str) and url and url not in seen_urls:
                        seen_urls.add(url)
                        clean_results.append(clean_result)
                        counts["news"] += 1

            if results.get("images"):
                images = results["images"]
                for image in images["items"]:
                    clean_result = {
                        "type": "image_url",
                        "image_url": image["url"],
                        "image_description": image["alt"],
                    }
                    url = clean_result["image_url"]
                    if isinstance(url, str) and url and url not in seen_urls:
                        seen_urls.add(url)
                        clean_results.append(clean_result)
                        counts["images"] += 1

        logger.debug(
            f"Results processing completed | "
            f"total_results={len(clean_results)} | "
            f"pages={counts['pages']} | "
            f"news_items={counts['news']} | "
            f"images={counts['images']} | "
            f"unique_urls={len(seen_urls)}"
        )

        return clean_results