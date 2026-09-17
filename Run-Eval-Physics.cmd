@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\eval_expertia_math.py --model C:\training\base\phi-4-mini-reasoning --val C:\training\datasets\expertia-physics-puro_val.jsonl --max-samples 500 --out C:\training\logs\eval_physics_base.json > C:\training\logs\eval_physics_base.log 2>&1
C:\training\python311\python.exe C:\training\eval_expertia_math.py --model C:\training\base\phi-4-mini-reasoning --adapter C:\training\adapters\expertia-physics-r16 --val C:\training\datasets\expertia-physics-puro_val.jsonl --max-samples 500 --out C:\training\logs\eval_physics_adapter.json > C:\training\logs\eval_physics_adapter.log 2>&1
echo EVAL DONE > C:\training\logs\eval_physics.done
