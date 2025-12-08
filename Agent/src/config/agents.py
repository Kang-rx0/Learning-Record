from typing import Literal

# 定义不同的LLM类型，基础，推理，具有视觉功能，代码生成功能
LLMType = Literal["basic", "reasoning", "vision", "code"]

# 为每个agent指定LLM类型
AGENT_LLM_MAP: dict[str, LLMType] = {
    "coordinator": "basic",
    "planner": "basic",
    "researcher": "basic",
    "analyst": "basic",
    "coder": "basic",
    "reporter": "basic",
    "podcast_script_writer": "basic",
    "ppt_composer": "basic",
    "prose_writer": "basic",
    "prompt_enhancer": "basic",
}