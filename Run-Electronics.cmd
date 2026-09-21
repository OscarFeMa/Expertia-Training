@echo off
setlocal
set TRAIN_STATUS_FILE=C:\training\logs\train_status.json
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe -u C:\training\train_expertia.py --model C:\training\base\phi-4-mini-reasoning --train C:\training\datasets\expertia-electronics-puro.jsonl --out C:\training\adapters\expertia-electronics-r16 --offload C:\training\offload --epochs 3 --seq-len 1024 --batch 1 --accum 16 --bf16 --save-steps 100 > C:\training\logs\train_electronics.log 2> C:\training\logs\train_electronics.err.log
