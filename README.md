# Learning
#### 记录一些从网上学习的代码笔记
- **LLM**：
    - Langchain
    - 微调：
      - Qwne, DeepSeek
      - Llama Factory；Unsloth
      - LoRA， QLoRA 

- **Agent**：
    - LangGraph
    - Deer Flow （https://github.com/bytedance/deer-flow）

- **前端**：
    - Vue3 + TypeScript

- **后端**：
    - FastAPI
    - Django（学习中）

- **强化学习** （学习中）

#### 文件结构
```
.
├── Agent/                  # 智能体相关学习
│   ├── note.md             # 笔记
│   └── src/                # 源码
│       ├── agents/         # 智能体实现
│       ├── config/         # 配置相关
│       ├── graph/          # 图结构
│       ├── llms/           # 大语言模型
│       ├── prompts/        # 提示模板
│       ├── tools/          # 工具
│       └── utils/          # 工具函数
│
├── Django/                 # Django官方文档学习笔记
│   ├── part1/ 到 part8/    # 各章节学习内容
│
├── fastapi/                # FastAPI学习代码
│   ├── 表单和文件.ipynb     # 表单和文件处理
│   ├── 请求体参数.ipynb     # 请求体参数学习
│   ├── 响应.ipynb          # 响应处理
│   ├── 依赖.ipynb          # 依赖注入
│   ├── request.ipynb       # 请求处理
│   ├── url参数.ipynb       # URL参数
│   └── 多人聊天室项目/      # 基于FastAPI实现的多人聊天室
│
├── FineTune/               # 模型微调相关
│   ├── DeepSeek-R1-Distill/ # 基于 DeepSeek-R1-Distill模型在医疗数据集的LoRA微调
│   ├── LoRA/               # LoRA微调
│   ├── Qwen/               # Qwen模型微调
│   └── XiaoHongShu/        # 基于 DeepSeek-R1 微调的小红书风格模型
│
├── Langchain/              # LangChain学习笔记
│   ├── Agent.ipynb         # 智能体
│   ├── LangChain01.ipynb 到 LangChain09.ipynb # 各章节学习
│   └── output.txt          # 输出文件
│
├── Qwen/                   # 基于Qwen的前后端项目 （全python实现）
│   ├── Back.py             # 后端代码
│   ├── Front.py            # 前端代码
│   ├── Qwen.ipynb          # （另外三个python文件的整合，用于输出调试）
│   └── Web.py              # 网页相关
│
├── RL/                     # 强化学习
│   ├── DQN.ipynb         
│   ├── Double DQN.ipynb         
│
├── Vue/                    # Vue3 + TypeScript学习
│   ├── src/                # 各个功能的学习笔记
│   ├── public/             # 公共资源
│   └── package.json        # 项目配置
│
└── README.md               # 项目说明
```
