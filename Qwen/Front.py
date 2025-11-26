import requests
import logging
from typing import Optional, List, Dict, Mapping, Any
import langchain
from langchain.llms.base import LLM
from langchain_community.cache import InMemoryCache

from typing import ClassVar

logging.basicConfig(level=logging.INFO)
langchain.llm_cache = InMemoryCache()


class ChatLLM(LLM):
    url: ClassVar[str] = "http://127.0.0.1:8000/chat"
    history: ClassVar[list] = []
    api_key: Optional[str] = None

    @property
    def _llm_type(self) -> str:
        return "qwen-3.0"  # 修改为对应模型名称

    def _construct_query(self, prompt: str) -> Dict:
        query = {
            "history": self.history,
            "query": prompt
        }
        import json
        query = json.dumps(query)
        return query

    @classmethod
    def _post(self, url: str, query: Dict) -> Any:
        key = ""
        headers = {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=query).json()
        return response

    def _call(self, prompt: str, stop: Optional[List[str]] = None, api_key: Optional[str] = None) -> str:
        query = self._construct_query(prompt=prompt)
        response = self._post(url=self.url, query=query)
        #print("后端返回：", response)  # 调试用，这个会返回所有：think，content，full content
        response_chat = response.get('content', '')  # 取 content 字段
        ChatLLM.history = response.get('history', ChatLLM.history) # 如果没有 history 字段则保持原样
        return response_chat

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        _param_dict = {
            "url": self.url
        }
        return _param_dict


if __name__ == "__main__":
    llm = ChatLLM()
    while True:
        user_input   = input("我: ")
        response = llm(user_input)
        print(f"ChatGLM: {response}")