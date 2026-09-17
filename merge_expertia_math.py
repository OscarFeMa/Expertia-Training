from pathlib import Path
base = r'C:\training\base\phi-4-mini-reasoning'
adapter = r'C:\training\adapters\expertia-math-r16'
out = r'C:\training\merged\expertia-math-fp16'
print('MERGE start', base, '->', out)
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True, use_fast=False)
model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float16, trust_remote_code=True, device_map='cpu')
print('base loaded')
model = PeftModel.from_pretrained(model, adapter)
print('adapter loaded')
model = model.merge_and_unload()
print('merged')
Path(out).mkdir(parents=True, exist_ok=True)
model.save_pretrained(out, safe_serialization=True)
tok.save_pretrained(out)
print('saved', out)
