Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$py='C:\training\python311\python.exe'
$root='C:\training'
if (!(Test-Path $py)) { $py="$root\python311\python.exe" }
if (!(Test-Path $py)) { $py=(Get-Command python -ErrorAction SilentlyContinue).Source }
Write-Host "== 1/4 MERGE LoRA -> FP16 ==" -F Cyan
if (!(Test-Path "$root\merge_expertia.py")) { try { Invoke-WebRequest http://192.168.1.42:8000/merge_expertia.py -OutFile "$root\merge_expertia.py" -UseBasicParsing } catch { Copy-Item "D:\proyectos\expertia\training\merge_expertia.py" "$root\merge_expertia.py" -Force -ErrorAction SilentlyContinue } }
& $py "$root\merge_expertia.py" --domain math
if ($LASTEXITCODE -ne 0) { throw "merge failed $LASTEXITCODE" }
Write-Host "== 2/4 GGUF F16 ==" -F Cyan
$llama="$root\llama.cpp"
if (!(Test-Path $llama)) { git clone https://github.com/ggerganov/llama.cpp $llama; Set-Location $llama; git pull } else { Set-Location $llama; git pull }
$hfOut="$root\merged\expertia-math-fp16"
$ggufF16="$root\merged\expertia-math-f16.gguf"
$env:PYTHONPATH="$llama"
& $py "$llama\convert_hf_to_gguf.py" $hfOut --outfile $ggufF16 --outtype f16
if (!(Test-Path $ggufF16)) { Set-Location $llama; & $py "convert_hf_to_gguf.py" $hfOut --outfile $ggufF16 --outtype f16 }
if (!(Test-Path $ggufF16)) { throw "GGUF F16 not created" }
Get-Item $ggufF16 | Format-Table Length,FullName
Write-Host "== 3/4 BUILD llama-quantize ==" -F Cyan
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
cmake --build build --config Release -j 4 --target llama-quantize
$exe=(Get-ChildItem -Recurse -Filter llama-quantize.exe | Select-Object -First 1).FullName
if (!(Test-Path $exe)) { throw "llama-quantize.exe not found" }
Write-Host "exe=$exe"
Write-Host "== 4/4 QUANTIZE Q4_K_M ==" -F Cyan
$ggufQ4="$root\merged\expertia-math-q4_k_m.gguf"
& $exe $ggufF16 $ggufQ4 Q4_K_M
Get-Item $ggufQ4 | Format-Table Length,FullName
Write-Host "== DONE PostTrain ==" -F Green
Write-Host "F16: $ggufF16"
Write-Host "Q4:  $ggufQ4"
Write-Host "Next: ollama create ExpertiaMath -f Modelfile"
