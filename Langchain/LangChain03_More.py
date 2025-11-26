"""
在 LangChain03.ipynb 的基础上，实现了一个基于Gradio的多轮对话机器人

通过gr.State()对象储存我们的对话列表状态，同时在事件绑定中将State对象作为输入和输出。
如submit.click(respond, [msg, chatbot, state], [msg, chatbot, state])函数，将发送消息按钮与respond函数绑定,
[msg, chatbot,state]与respond函数的输入参数绑定，respond函数的返回值给下一状态[msg, chatbot,state]赋值。
msg绑定了用户输入消息栏的内容，chatbot绑定了对话栏内容。
流式响应函数支持async流式输出, 使用async for循环来获取模型astream的异步输出即可。
同时这里使用yield生成器实时反馈到前端。
"""


import gradio as gr
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ──────────────────────────────────────────────
# 1. 模型、Prompt、Chain
# ──────────────────────────────────────────────

model = init_chat_model(
    model="Qwen/Qwen3-8B",
    model_provider="openai",
    base_url="https://api.siliconflow.cn/v1/",
    api_key="",
)
parser = StrOutputParser()

chatbot_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content="你是一名智能助手，能够回答或是解决user发的内容。"),
        MessagesPlaceholder(variable_name="messages"),  # 手动传入历史
    ]
)

qa_chain = chatbot_prompt | model | parser   # LCEL 组合

# ──────────────────────────────────────────────
# 2. Gradio 组件
# ──────────────────────────────────────────────
CSS = """
.main-container {max-width: 1200px; margin: 0 auto; padding: 20px;}
.header-text {text-align: center; margin-bottom: 20px;}
"""

def create_chatbot():
    with gr.Blocks(title="聊天机器人", css=CSS) as demo:
        with gr.Column(elem_classes=["main-container"]):
            gr.Markdown("#   LangChain智能对话机器人系统", elem_classes=["header-text"])

            chatbot = gr.Chatbot(
                height=500,
                show_copy_button=True,
                avatar_images=(
                    "https://cdn.jsdelivr.net/gh/twitter/twemoji@v14.0.2/assets/72x72/1f464.png",
                    "https://cdn.jsdelivr.net/gh/twitter/twemoji@v14.0.2/assets/72x72/1f916.png",
                ),
            )
            msg = gr.Textbox(placeholder="请输入您的问题...", container=False, scale=7)
            submit = gr.Button("发送", scale=1, variant="primary")
            clear = gr.Button("清空", scale=1)

        # ---------------  状态：保存 messages_list  ---------------
        state = gr.State([])          # 这里存放真正的 Message 对象列表

        # ---------------  主响应函数（流式） ----------------------
        async def respond(user_msg: str, chat_hist: list, messages_list: list):
            # 1) 输入为空直接返回
            if not user_msg.strip():
                yield "", chat_hist, messages_list
                return

            # 2) 追加用户消息
            messages_list.append(HumanMessage(content=user_msg))
            chat_hist = chat_hist + [(user_msg, None)]
            yield "", chat_hist, messages_list      # 先显示用户消息

            # 3) 流式调用模型
            partial = ""
            async for chunk in qa_chain.astream({"messages": messages_list}):
                partial += chunk
                # 更新最后一条 AI 回复
                chat_hist[-1] = (user_msg, partial)
                yield "", chat_hist, messages_list

            # 4) 完整回复加入历史，裁剪到最近 50 条
            messages_list.append(AIMessage(content=partial))
            messages_list = messages_list[-50:]

            # 5) 最终返回（Gradio 需要把新的 state 传回）
            yield "", chat_hist, messages_list

        # ---------------  清空函数 -------------------------------
        def clear_history():
            return [], "", []          # 清空 Chatbot、输入框、messages_list

        # ---------------  事件绑定 ------------------------------
        msg.submit(respond, [msg, chatbot, state], [msg, chatbot, state])
        submit.click(respond, [msg, chatbot, state], [msg, chatbot, state])
        clear.click(clear_history, outputs=[chatbot, msg, state])

    return demo

# ──────────────────────────────────────────────<br/># 3. 启动应用<br/># ──────────────────────────────────────────────
demo = create_chatbot()
demo.launch(server_name="0.0.0.0", server_port=7860, share=False, debug=True)