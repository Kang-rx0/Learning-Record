from modelscope.hub.snapshot_download import snapshot_download
model_dir = snapshot_download("unsloth/DeepSeek-R1-Distill-Llama-8B",cache_dir = "/model")