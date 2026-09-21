@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\llama.cpp\convert_hf_to_gguf.py C:\training\merged\expertia-swe-fp16 --outfile C:\training\merged\expertia-swe-f16.gguf --outtype f16 > C:\training\logs\gguf_swe.log 2>&1
C:\training\llama-bin-b10855\llama-quantize.exe C:\training\merged\expertia-swe-f16.gguf C:\training\merged\expertia-swe-q4_k_m.gguf Q4_K_M > C:\training\logs\quant_swe.log 2>&1
echo GGUF DONE > C:\training\logs\gguf_swe.done
