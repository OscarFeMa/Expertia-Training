@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\eval_expertia.py --model C:\training\base\phi-4-mini-reasoning --val C:\training\datasets\expertia-chemistry-puro_val.jsonl --max-samples 500 --out C:\training\logs\eval_chemistry_base.json > C:\training\logs\eval_chemistry_base.log 2>&1
C:\training\python311\python.exe C:\training\eval_expertia.py --model C:\training\base\phi-4-mini-reasoning --adapter C:\training\adapters\expertia-chemistry-r16 --val C:\training\datasets\expertia-chemistry-puro_val.jsonl --max-samples 500 --out C:\training\logs\eval_chemistry_adapter.json > C:\training\logs\eval_chemistry_adapter.log 2>&1
echo EVAL DONE > C:\training\logs\eval_chemistry.done
