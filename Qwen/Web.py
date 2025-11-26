import gradio as gr
from Front import ChatLLM #引用Front.py里面我们定义的ChatLLM

# llm = ChatLLM()
# # 流式处理
# def stream_translate(text):
#     response = llm(text)
#     for chunk in response.split():
#         yield chunk + " "


# demo = gr.Interface(fn=stream_translate, inputs="text", outputs="text", title="ChatGLM",
#                     description="A chatbot powered by ChatGLM.")
# demo.launch()


# 流式处理
def stream_translate(messages,history):
    llm = ChatLLM()
    response = llm(messages)
    # for chunk in response.split():
    #     yield chunk + " "
    return response
gr.ChatInterface(
    stream_translate,
    type="messages",
).launch()