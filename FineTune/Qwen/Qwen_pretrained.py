"""

"""

from modelscope.hub.snapshot_download import snapshot_download

model_dir = snapshot_download("Qwen/Qwen2.5-1.5B", cache_dir = "E:\pythonCode\FineTune\Qwen\Qwen2.5_1.5B")

print(model_dir)