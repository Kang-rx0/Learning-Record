# https://zhuanlan.zhihu.com/p/24874356260

#################################################### <start> 配置 HuggingFace 和 WandB <start> ####################################################
from huggingface_hub import login
hf_token = "XXX"  #到官网免费申请一个
login(hf_token)

import wandb
wb_token = "XXX"  #到官网免费申请一个
wandb.login(key=wb_token)
run = wandb.init(
    project='fine-tune-DeepSeek-R1-Distill-Qwen-14B on xhs Dataset',
    job_type="training",
    anonymous="allow"
)
#################################################### </end> 配置 HuggingFace 和 WandB </end> ####################################################
#************************************************************************************************************************************************

#################################################### <start> 加载模型和分词器 <start> ####################################################
#************************************************************************************************************************************************
from unsloth import FastLanguageModel

max_seq_length = 2048
dtype = None
load_in_4bit = True
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/DeepSeek-R1-Distill-Qwen-14B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,  # 4bit量化加载
    token = hf_token,
)
#################################################### </end> 加载模型和分词器 </end> ####################################################
#************************************************************************************************************************************************

#################################################### <start> 训练模版 <start> ####################################################
#************************************************************************************************************************************************

train_prompt_style = """
以下是一项任务说明，并附带了更详细的背景信息。
请撰写一个满足完成请求的回复。
在回答之前，请仔细考虑问题，并创建一个逐步的思考链，以确保逻辑和准确的回答。

### Instruction:
你是一个资深的小红书文案专家
请你根据以下问题完成写作
### Question:
{}
### Response:
<think>
{}
</think>n:
"""
EOS_TOKEN = tokenizer.eos_token
#################################################### </end> 训练模版 </end> ####################################################
#************************************************************************************************************************************************

#################################################### <start> 定义函数，让数据集填入模版 <start> ####################################################
#************************************************************************************************************************************************

import re  # 导入正则表达式模块
# 使用正则提取思考链和最终响应
def formatting_prompts_func(examples):
    # 提取数据集里的 instructions 和 outputs （本次数据集的 think 部分融合在 outputs 里）
    instructions = examples["instruction"]
    outputs = examples["output"]
    texts = []
    # 在for循环中使用zip()函数来并行迭代多个可迭代的对象
    for instruction_text, output_text in zip(instructions, outputs):
        # 使用正则表达式提取 outputs 里 <think> 和 </think> 之间的内容作为 cots
        match = re.search(r"<think>(.*?)</think>", output_text, re.DOTALL)
        cot = match.group(1).strip() if match else ""

        # 提取 </think> 之后的内容作为 outputs
        output = output_text.replace(match.group(0), "").strip() if match else output_text.strip()

        text = train_prompt_style.format(instruction_text, cot, output) + EOS_TOKEN
        texts.append(text)
    return {"text": texts}
#################################################### </end> 定义函数，让数据集填入模版 </end> ####################################################
#************************************************************************************************************************************************

#################################################### <start> 读取数据集，应用上面定义的函数 <start> ####################################################
#************************************************************************************************************************************************

from datasets import load_dataset

data_files = r'E:\pythonCode\FineTune\XiaoHongShu\Dataset\xhs_data.json'
dataset = load_dataset("json", data_files=data_files, split="train")

# 使用 map 函数进行数据处理
dataset = dataset.map(formatting_prompts_func, batched=True)
#################################################### </end> 读取数据集，应用上面定义的函数 </end> ####################################################
#************************************************************************************************************************************************

#################################################### <start> 设置LoRA参数 <start> ####################################################
#************************************************************************************************************************************************

model = FastLanguageModel.get_peft_model(
    model,
    r = 32, # rank of LoRA
    target_modules = [
        "q_proj", 
        "k_proj", 
        "v_proj", 
        "o_proj", 
        "gate_proj", 
        "up_proj", 
        "down_proj", 
        "fc1", 
        "fc2"], # Qwen-14B的适配
    lora_alpha = 32, # 缩放因子
    lora_dropout = 0,
    bias = 'none',
    use_grad_checkpoint = "unsloth", # gradient checkpointing 节省显存
    random_state = 42,
    use_rslora = True,  # 使用随机LoRA
    loftq_config = None, # 不使用LoFTQ
)
'''
loftq_config 说明：
    LoftQ 是一种结合量化和低秩分解（LoRA）的参数高效微调技术，
    旨在通过初始化 LoRA 权重来最小化量化误差，从而提高量化模型在微调时的性能
    详见：https://blog.csdn.net/u013172930/article/details/147375738
'''
#################################################### </end> 设置LoRA参数 </end> ####################################################
#************************************************************************************************************************************************

#################################################### <start> 配置 SFTTrainer 训练器 <start> ####################################################
#************************************************************************************************************************************************
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,       #输入序列的最大长度
    dataset_num_proc=2,                #预处理数据集的进程数
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,  #梯度累积步数（变相模拟更大batch_size）
        warmup_steps=5,         #学习率预热步数。
        max_steps=200,         # 总训练步数
        learning_rate=2e-4,    #学习率
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,          # 权重衰减系数
        lr_scheduler_type="linear", #学习率调度器
        seed=6666,                #选一个自己喜欢的随机数种子
        output_dir="outputs",
        report_to="wandb",       # 使用 wandb 进行报告,实验指标可视化
    ),
)
#################################################### </end> 配置 SFTTrainer 训练器 </end> ####################################################
#************************************************************************************************************************************************

train_state = trainer.train()