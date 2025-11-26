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

save_file = r'E:\pythonCode\FineTune\XiaoHongShu\Dataset\xhs_data.json'
save_to_json(filtered_dataset['train'], save_file)


print(f"数据已保存到 {save_file}")