# coding=utf-8
"""
代码改自 https://deepseek.csdn.net/67c16b806670175f992cf2e4.html
在A5000 24GB上跑的，batch_size=32，gradient_accumulation=4，微调5个epoch, 显存占用19GB
耗时2:11:39

自定义语言模版，并使数据集适应该语言模版。用peft加SFTTrainer进行LoRA微调
SFTTrainer支持两种数据集形式：
            - [Standard](dataset_formats#standard): Each sample contains plain text.
            - [Conversational](dataset_formats#conversational): Each sample contains structured messages (e.g., roleand content).
这里用的是Standard形式，详见下面数据集处理部分，添加了text字段

需要创建 model，logs，outputs 三个文件夹
数据集默认跟该文件放在同一级

# 安装unsloth包（大型语言模型微调工具）
pip install unsloth

# 卸载旧版本并安装最新版unsloth（GitHub源码）
pip uninstall unsloth -y && pip install --upgrade --no-cache-dir --no-deps git+https://github.com/unslothai/unsloth.git
pip install swanlab
# 安装量化工具包
pip install bitsandbytes unsloth_zoo
pip install modelscope
pip install transformers
却什么就安装什么，建议torch版本大于2.0
数据集从huggingface下载：medical_o1_sft_Chinese.json，40多MB
"""

import torch
import torch.nn as nn
from unsloth import FastLanguageModel
from trl import SFTTrainer
import swanlab
from datasets import load_dataset
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported
from swanlab.integration.transformers import SwanLabCallback
import os

print("GPU using: ",torch.cuda.device_count())

###################################################################################################################################################################################################
# ----------------------------------------------------------------------- Download Model <start>-----------------------------------------------------------------------
###################################################################################################################################################################################################
print("\n-------------------------------------------------------------- Download Model --------------------------------------------------------------\n")
from modelscope.hub.snapshot_download import snapshot_download
model_dir = snapshot_download("unsloth/DeepSeek-R1-Distill-Llama-8B",cache_dir = "/model")
print("\n-------------------------------------------------------------- Model Downloaded --------------------------------------------------------------\n")
###################################################################################################################################################################################################
# ----------------------------------------------------------------------- Download Model <end>-----------------------------------------------------------------------
###################################################################################################################################################################################################


###################################################################################################################################################################################################
# ----------------------------------------------------------------------- SwanLab Setting <start>-----------------------------------------------------------------------
###################################################################################################################################################################################################
# 这里用swanlab记录实验日志，也可以用wandb
# 因训练调用 SFTTrainer，所以这里的日志记录是通过在SFTTrainer里的callbacks里添加SwanLabCallback实现
# 外部这里是初始化，也可以直接在 SFTTrainer 里初始化

swanlab.login(api_key="", save=True)  # ！！！！！！！！！！！！！！！ 填写API Key ！！！！！！！！！！！！！！！
swanlab.init(
    # 设置项目
    project="Finetune-DeepSeek-R1-Distill-Llama-8B-with-medical-data",
    experiment_name = "Test1",
    logdir = "/logs",
    # 跟踪超参数与实验元数据
    config={
        "learning_rate": 2e-4,
        "architecture": "DeepSeek-R1-Distill-Llama-8B",
        "dataset": "medical_o1_sft_Chinese.json",
        "optim": "adamw_8bit"
    }
)
###################################################################################################################################################################################################
# ----------------------------------------------------------------------- SwanLab Setting <end>-----------------------------------------------------------------------
###################################################################################################################################################################################################

max_seq_length = 2048        # 模型处理文本的最大长度（上下文窗口）
dtype = None                 # 自动选择计算精度（通常为float16或bfloat16）
load_in_4bit = True          # 启用4位量化压缩，减少显存占用
print("\n-------------------------------------------------------------- Loading Model --------------------------------------------------------------\n")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/gz-data/model/unsloth/DeepSeek-R1-Distill-Llama-8B",  # 模型名称
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit
)
print("\n-------------------------------------------------------------- Model Loaded ---------------------------------------------------------------\n")

###################################################################################################################################################################################################
# ----------------------------------------------------------------------- 这一部分只是在测试微调前的输出 <start>-----------------------------------------------------------------------
###################################################################################################################################################################################################

# prompt_style = """以下是描述任务的指令，附带提供更多背景信息的输入。
# 请撰写一个恰当完成要求的回答。
# 在回答前，请仔细思考问题并建立分步推理链，以确保回答的逻辑性和准确性。

# ### 指令:
# 您是一位在临床推理、诊断和治疗方案制定方面具有专业知识的医学专家。
# 请回答以下医学问题。

# ### 问题:
# {}

# ### 回答:
# <思考>{}"""

# question = "一位23岁的女性患者在进行烤瓷冠修复后,发现瓷层的颜色缺乏层次感。造成这种现象的最常见原因是什么？"
# response = "A test response"

# FastLanguageModel.for_inference(model)  # 推理，把训练好的模型切换到 推理模式，并自动开启 2× 加速。

# inputs = tokenizer([prompt_style.format(question, "")], return_tensors="pt").to("cuda")

#################################################################- Note <start> -#######################################################
# prompt_style.format方法自动将变量question和""填充到prompt_style里的两个{}位置
# 用question的内容填充###问题：里的第一个{}，用空""来填充###回答： 处的{}
# inputs store indexs after tonkenize
'''
inputs = {input_ids:tensor([[id1,id2,...]]),         input_ids是每个token对应的索引
      attention_mask:tensor([[mask1,mask2,...]])}    attention_mask是一个与输入序列等长的二进制掩码（0/1组成），
                                                        其中1表示对应位置的token需参与注意力计算。
                                                        0表示该位置可被忽略（如填充token），以避免模型学习无效信息。
'''
####################################################################- Note <end> -#############################################

# outputs = model.generate(
#     input_ids=inputs.input_ids,
#     attention_mask=inputs.attention_mask,
#     max_new_tokens=1200,
#     use_cache=True,
# )

# output 返回的也是一堆索引，要用tokenizer.batch_decode来解码

# response = tokenizer.batch_decode(outputs)

# 解码后的reponse是一个数组，内容是以<｜begin▁of▁sentence｜>开头，后面接的是prompt_style里的内容，{}部分被替换为问题和模型的回答
# 因此下面提取 “### 回答: ” 的内容作为模型输出 （这是prompt_style里自定义的）

# print(response[0].split("### 回答:")[1])

# 模型返回 <思考>....回答.....<思考>

###################################################################################################################################################################################################
# ----------------------------------------------------------------------- 这一部分只是在测试微调前的输出 <end>-----------------------------------------------------------------------
###################################################################################################################################################################################################

print("\n-------------------------------------------------------------- Load LoRA --------------------------------------------------------------\n")

model = FastLanguageModel.get_peft_model(  # get_peft_model方法可以调用模型，并且在指定位置添加LoRA适配器
    
    model,  # 预加载的基座模型

    # 低秩适配参数配置
    r=16,  # 低秩矩阵的维度(秩)，设置秩r=16表示分解矩阵形状为(d×16)和(16×d)
    lora_alpha=16,  # 缩放因子，控制低秩矩阵的更新幅度，实际缩放系数s=alpha/r=1.0

    # 目标模块选择（要微调的模块）
    target_modules=[
        "q_proj",  # Query投影层(注意力机制核心组件)
        "k_proj",  # Key投影层
        "v_proj",  # Value投影层
        "o_proj",  # 注意力输出层
        "gate_proj",  # FFN门控层(SwiGLU激活函数)
        "up_proj",  # FFN升维层
        "down_proj",  # FFN降维层
    ],  # 覆盖Transformer所有核心运算模块

    # 正则化配置
    lora_dropout=0,  # 关闭LoRA层的Dropout(适用于小数据集场景)
    bias="none",  # 不训练原始模型的偏置参数

    # 显存优化配置
    use_gradient_checkpointing="unsloth",  # 启用Unsloth特化梯度检查点技术

    # 随机性与初始化
    random_state=3407,  # 固定随机种子保证实验可复现
    use_rslora=False,  # 禁用RS-LoRA的缩放约束
    loftq_config=None,  # 不使用LoftQ量化感知初始化
)
print("\n-------------------------------------------------------------- LoRA Loaded --------------------------------------------------------------\n")
# 微调数据的处理
train_prompt_style = """以下是描述任务的指令，附带提供更多背景信息的输入。
请撰写一个恰当完成要求的回答。
在回答前，请仔细思考问题并建立分步推理链，以确保回答的逻辑性和准确性。

### 指令:
您是一位在临床推理、诊断和治疗方案制定方面具有专业知识的医学专家。
请回答以下医学问题。

### 问题:
{}

### 回答:
<think>
{}
</think>
{}"""
# 这的模版多了<think>{}</think>的部分，用于存储思考过程的内容，这是根据数据集来设定的
# 因为数据集每条数据包含了 {"Question":... , "Complex_CoT":.... , "Response":...}

print("\n-------------------------------------------------------------- Process Data --------------------------------------------------------------\n")
EOS_TOKEN = tokenizer.eos_token  # Must add EOS_TOKEN 这是结尾标记 <｜end▁of▁sentence｜>
def formatting_prompts_func(examples):
    inputs = examples["Question"]
    cots = examples["Complex_CoT"]
    outputs = examples["Response"]
    texts = []
    for input, cot, output in zip(inputs, cots, outputs):
        text = train_prompt_style.format(input, cot, output) + EOS_TOKEN
        texts.append(text)
    return {
        "text": texts,
    }
# 结果处理后，就把Question，Complex_CoT，Response填充到模版里的三个{}里，返回为text

dataset = load_dataset("json", data_files="/gz-data/medical_o1_sft_Chinese.json", split="train[0:2500]")   # 共有5000条数据，实际上数据规模并不大

dataset = dataset.map(formatting_prompts_func, batched = True,)
print("\n -------------------------------------------------------------- Data Processed --------------------------------------------------------------\n")
"""
原始是：
[
  {'Question': '....', 'Complex_CoT': '....', 'Response': '....'},
  {'Question': '....', 'Complex_CoT': '....', 'Response': '....'},
]
通过使用load dataset函数读取后，会自动处理成：
{
"Question":['....','.....','....'],
"Complex_CoT":['....','.....','....'],
"Response":['....','.....','....']
}
然后用自定义的函数有在数据集基础上加入了一个 text 键，值是完整的train_prompt_style
即用Question，Complex_CoT，Response填充后的完整句子
{
"Question":['....','.....','....'],
"Complex_CoT":['....','.....','....'],
"Response":['....','.....','....'],
"text":['....','.....','....']
}
"""
# dataset[:6]

# 设置训练参数并开始训练
trainer = SFTTrainer(
    # 基础配置
    model=model,          # 已加载的基座模型（含LoRA适配器）
    tokenizer=tokenizer,  # 与模型匹配的分词器
    train_dataset=dataset, # 预处理后的训练数据集

    # 数据处理参数
    dataset_text_field="text",      # 指定文本字段（包含格式化指令）
    max_seq_length=2048,           # 序列最大长度（需匹配模型预训练长度）
    dataset_num_proc=2,           # 数据预处理并行进程数

    # 训练参数配置
    args=TrainingArguments(
        # 批次与显存优化
        # 有效批量 = per_device_batch × gradient_accumulation × num_gpus, 这里没有设置num gpus
        per_device_train_batch_size=32,    # 单GPU批次大小（根据显存调整）   # 2+4,占8GB； 6+4占11GB；6+12占5GB； 12占15GB；32+4 占19GB
        gradient_accumulation_steps=4,    # 梯度累积步数（等效batch_size=32*4) 

        # 训练周期控制
        num_train_epochs=5,               # 遍历数据集 num_train_epochs 次就停止
        warmup_ratio=0.1,                # 学习率预热比例（前10% steps预热）

        # 优化器配置
        learning_rate=2e-4,             # 初始学习率（医学领域建议1e-5~5e-4）
        optim="adamw_8bit",             # 量化优化器（节省30%显存）
        weight_decay=0.01,              # L2正则化强度

        # 精度配置
        fp16=not is_bfloat16_supported(),  # FP16混合精度（优先使用BF16）
        bf16=is_bfloat16_supported(),      # BF16精度（需Ampere+架构GPU）

        # 日志与输出
        logging_steps=10,              # 每10步记录日志（监控梯度变化）
        lr_scheduler_type="linear",    # 线性学习率衰减
        seed=3407,                     # 随机种子（确保可复现性）
        output_dir="/gz-data/outputs",         # 检查点保存路径
    ),
    #callbacks=[SwanLabCallback(project="Finetune-DeepSeek-R1-Distill-Llama-8B-with-medical-data",experiment_name="Test1")]
    callbacks=[SwanLabCallback()]
)

print(" \n-------------------------------------------------------------- Start Training --------------------------------------------------------------\n")
trainer_stats = trainer.train()
print("\n -------------------------------------------------------------- Training Finished --------------------------------------------------------------\n")

print(" \n-------------------------------------------------------------- Save Model --------------------------------------------------------------\n")
# save model (original para and fine tuned para)
def mkdir(path):
 
    folder = os.path.exists(path)
 
    if not folder:                   
        os.makedirs(path)          
        print("---  new folder...  ---")
        print("---  OK  ---")
 
    else:
        print("---  Folder Exist  ---")
		
save_file = "/gz-data/save_model"
mkdir(save_file)

model.save_pretrained_merged(save_file, tokenizer, save_method = "merged_16bit")
print(" \n-------------------------------------------------------------- Model Saved --------------------------------------------------------------\n")

# swanlab.finish()