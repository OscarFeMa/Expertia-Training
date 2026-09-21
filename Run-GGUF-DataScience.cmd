@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\llama.cpp\convert_hf_to_gguf.py C:\training\merged\expertia-datascience-fp16 --outfile C:\training\merged\expertia-datascience-f16.gguf --outtype f16 > C:\training\logs\gguf_datascience.log 2>&1
C:\training\llama-bin-b10855\llama-quantize.exe C:\training\merged\expertia-datascience-f16.gguf C:\training\merged\expertia-datascience-q4_k_m.gguf Q4_K_M > C:\training\logs\quant_datascience.log 2>&1
echo GGUF DONE > C:\training\logs\gguf_datascience.done
