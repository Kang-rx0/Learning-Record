#****************************************************************************************************************************************************************
#************************************************************************    模型加载     ************************************************************************
#****************************************************************************************************************************************************************
# load the tokenizer and the model
from modelscope import AutoModelForCausalLM, AutoTokenizer
#model_name ="E:\Code\PythonCode\Qwen\model\Qwen\Qwen3-0___6B"
model_name = "E:\pythonCode\Qwen\model"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

#****************************************************************************************************************************************************************
#************************************************************************    后端接口     ************************************************************************
#****************************************************************************************************************************************************************


import uvicorn
from fastapi import FastAPI,Body
from fastapi.responses import JSONResponse
from typing import Dict
app = FastAPI()

@app.post("/chat")
def chat(data: dict = Body(...)):
    prompt = data.get("query")
    print("用户输入：", prompt)
    print("类型：", type(prompt))
    history = data.get("history", [])
    messages = [
    {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True # 切换是否为思考模式
        )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated = model.generate(
        **model_inputs,
        max_length=32768,
        num_return_sequences=1
        )
    output = generated[0][len(model_inputs.input_ids[0]):].tolist()
    try:
        # rindex finding 151668 (</think>)
        index = len(output) - output[::-1].index(151668)
    except ValueError:
        index = 0

    thinking_content = tokenizer.decode(output[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output[index:], skip_special_tokens=True).strip("\n")
    full_content = tokenizer.decode(output, skip_special_tokens=True).strip("\n")

    response = {'thinking content':thinking_content,'content':content,'full content':full_content}
    return JSONResponse(content=response)

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
    # 下面这是针对在jupyter notebook里启动uvicorn的
    # 否则会报错：RuntimeError: asyncio.run() cannot be called from a running event loop
    # config = uvicorn.Config(app, port=5000, log_level="info")
    # server = uvicorn.Server(config)
    # await server.serve()