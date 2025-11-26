![微调deepseek-R1模型应用实例-小红书文案推理数据集-变身文案大师](data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)

微调deepseek-R1模型应用实例-小红书文案推理数据集-变身文案大师
=====================================
1.前言
----

\~~~~~ 单纯和deepseek聊天，那很乏味了，让deepseek做某个垂直领域的专家，那可太有意思了。本期教程是在小红书推理思考数据集上微调DeepSeek-R1-Distill-Qwen-14B，让deepseek变成小红书文案大师，帮我们自动生成文案。当然，本教程仅仅作为一个引例，大家大可尝试不同的数据集，采用不同大小的蒸馏模型（如果你有几万张英伟达的GPU，建议你尝试更大的模型，站得高，看得远嘛doge）。此外，本篇文章的配套B站视频如下所示，大家可以一起讨论，如有错误，恳请批评指正。

\~~~~~ 还有一件事情，**下载数据集**到当前目录

```
from datasets import load_dataset
import json

# 加载数据集，使用 streaming=True 避免一次性下载全部数据
dataset = load_dataset("Congliu/Chinese-DeepSeek-R1-Distill-data-110k-SFT", streaming=True)

# 过滤数据，只保留 repo_name 为 'xhs/xhs' 的数据
filtered_dataset = dataset.filter(lambda example: example['repo_name'] == 'xhs/xhs')
#filtered_dataset = dataset['train'].filter(lambda example: example['repo_name'] == 'xhs/xhs')


# 将过滤后的数据保存为 JSON 文件
def save_to_json(dataset, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for example in dataset:
            #filtered_dataset是一个可迭代对象，需要逐条example提取
            json.dump(example, f, ensure_ascii=False)
            f.write('\n')  # 每条数据之间添加换行符


save_to_json(filtered_dataset['train'], 'xhs_data.json')


print("数据已保存到 xhs_data.json")
```

2.手把手微调代码讲解
-----------

### 2.1第一步，安装必要的库

\~~~~~ 其中unsloth这个框架可以使得微调任务更快，更省内存，wandb用来跟踪并可视化微调过程，比如train\_loss、GPU利用率

```
!pip install unsloth   # 高效微调框架，优化内存和训练速度
!pip install datasets
!pip install -U huggingface_hub
!pip install wandb    # 实验跟踪工具，如追踪train_loss，并可视化
```

\~~~~~ 下图是wandb追踪train\_loss的图片（我在4090上花了30分钟跑了200步）

![](https://pic2.zhimg.com/v2-99befd3bfc2e2029916eaceb8f14fa71_1440w.jpg)

wandb-train\_loss

### 2.2第二步，配置hugging face的Access Tokens

\~~~~~ 配置这玩意，待会要从hugging face下载模型，要申请token，可以到官网免费申请

```
# 登录HuggingFace Hub，待会要下载模型
from huggingface_hub import login
hf_token = "XXX"  #到官网免费申请一个
login(hf_token)     
```

### 2.3第三步，初始化wandb

配置这玩意，跟踪训练过程并可视化，又要申请token，可以到官网免费申请

```
import wandb

wb_token = "XXX"  #到官网免费申请一个
wandb.login(key=wb_token)
run = wandb.init(
    project='fine-tune-DeepSeek-R1-Distill-Qwen-14B on xhs Dataset',
    job_type="training",
    anonymous="allow"
)
```

### 2.4第四步，加载模型和对应的分词器

\~~~~~ 我这里使用的是一个14B的蒸馏模型，训练过程用了16G的显存，你有计算资源可以用大一点的模型。

```
from unsloth import FastLanguageModel

max_seq_length = 2048
dtype = None
load_in_4bit = True
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/DeepSeek-R1-Distill-Qwen-14B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,  # 4bit量化加载以节省显存
    token = hf_token,
)
```

### 2.5第五步，定义训练时prompt模板

\~~~~~ 本例中，我的任务是让deepseek变成小红书文案专家。当然，你如果有不同的数据集，做不同的任务，这里需要更改。

```
train_prompt_style = """以下是一项任务说明，并附带了更详细的背景信息。
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
</think>
{}"""
EOS_TOKEN = tokenizer.eos_token
```

### 2.6第六步，对数据进行处理与标准化（重点）

\~~~~~ 这一部分跟你的数据集息息相关，不同的数据集可能数据结构不一样，数据处理的函数需要你自己编写。

我这个小红书推理数据集是一个**已经下载到当前目录的json文件**，数据结构如下所示：

![](https://pica.zhimg.com/v2-5b93159499e3089fd99df5fb4b28e42c_1440w.jpg)

```
import re  # 导入正则表达式模块
# 使用正则提取思考链和最终响应
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    outputs = examples["output"]
    texts = []
    for instruction_text, output_text in zip(instructions, outputs):
        # 使用正则表达式提取 <think> 和 </think> 之间的内容作为 cots
        match = re.search(r"<think>(.*?)</think>", output_text, re.DOTALL)
        cot = match.group(1).strip() if match else ""

        # 提取 </think> 之后的内容作为 outputs
        output = output_text.replace(match.group(0), "").strip() if match else output_text.strip()

        text = train_prompt_style.format(instruction_text, cot, output) + EOS_TOKEN
        texts.append(text)
    return {"text": texts}
```

### 2.7第七步，加载数据集，并使用上面的函数处理

```
# 加载数据集
from datasets import load_dataset

dataset = load_dataset("json", data_files="xhs_data.json", split="train")

# 使用 map 函数进行数据处理
dataset = dataset.map(formatting_prompts_func, batched=True)
```

### 2.8第八步，设置 LoRA 进行微调

\~~~~~ 其中r是lora\_rank，值越大，更新的参数量越多，训练越慢，效果更好。lora\_alpha用来控制参数值的更新幅度

```
model = FastLanguageModel.get_peft_model(
    model,
    r=32,  # LoRA秩（矩阵分解维度）
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_alpha=32,  # 缩放因子
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=6666,
    use_rslora=False,
    loftq_config=None,
)
```

### 2.9第九步，配置训练器，准备训练

\~~~~~ 能调的一些参数我都注释出来了

```
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
```

### 2.10第十步，训练

```
trainer_stats = trainer.train()
```

3.结果及效果演示
---------

\~~~~~ 使用4090训练了200步，train\_loss曲线如下所示，我们可以看到，损失一直在降低，仍有下降空间，继续训练效果会更好一些。

![](https://pic2.zhimg.com/v2-99befd3bfc2e2029916eaceb8f14fa71_1440w.jpg)

\~~~~~ 光有这个train\_loss不过瘾啊，我们看看模型微调后的回答。

我们先设置一个用于提问的prompt。

```
prompt_style = """以下是一项任务说明，并附带了更详细的背景信息。
请撰写一个满足完成请求的回复。
在回答之前，请仔细考虑问题，并创建一个逐步的思考链，以确保逻辑和准确的回答。

### Instruction:
你是一个资深的小红书文案专家
请你根据以下问题完成写作
### Question:
{}
### Response:
<think>{}"""
```

接下来，调用我们微调后的模型，问问题（提要求）。

我提的要求是：“写一篇小红书风格的帖子，标题是男生变帅只需三步丨分享逆袭大干货 ”

```
question = "写一篇小红书风格的帖子，标题是男生变帅只需三步丨分享逆袭大干货  "


FastLanguageModel.for_inference(model)
inputs = tokenizer([prompt_style.format(question, "")], return_tensors="pt").to("cuda")
outputs = model.generate(
    input_ids=inputs.input_ids,
    attention_mask=inputs.attention_mask,
    max_new_tokens=1200,
    use_cache=True,
)
response = tokenizer.batch_decode(outputs)
print(response[0].split("### Response:")[1])
```

我们看看模型的思考过程，这考虑的是面面俱到啊

![](https://picx.zhimg.com/v2-30046a47c1349acf24bcee796043fda9_1440w.jpg)

再来看一下最后回答，（图片没截完，下面还有一大堆），我们可以看到，这满满的小红书味道啊！

![](https://pic2.zhimg.com/v2-18696e49109c248ed913806810369cd3_1440w.jpg)
