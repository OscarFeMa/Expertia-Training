Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root='C:\training'
$llama="$root\llama.cpp"
$ggufF16="$root\merged\expertia-math-f16.gguf"
$ggufQ4="$root\merged\expertia-math-q4_k_m.gguf"
if (!(Test-Path $ggufF16)) { $ggufF16='D:\training\merged\expertia-math-f16.gguf'; $ggufQ4='D:\training\merged\expertia-math-q4_k_m.gguf' }
Write-Host "== check tools =="
git --version; cmake --version; nvidia-smi --query-gpu=driver_version --format=csv,noheader
if (!(Test-Path $llama)) { Write-Host "cloning llama.cpp"; git clone https://github.com/ggerganov/llama.cpp $llama }
Set-Location $llama
git pull
Write-Host "== build llama-quantize (CPU) =="
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
cmake --build build --config Release -j 4 --target llama-quantize
$exe="$llama\build\bin\Release\llama-quantize.exe"
if (!(Test-Path $exe)) { $exe="$llama\build\bin\llama-quantize.exe" }
if (!(Test-Path $exe)) { $exe=(Get-ChildItem -Recurse -Filter llama-quantize.exe | Select-Object -First 1).FullName }
Write-Host "exe=$exe"
if (!(Test-Path $exe)) { throw "llama-quantize.exe not found" }
Write-Host "== quantize F16 -> Q4_K_M =="
& $exe $ggufF16 $ggufQ4 Q4_K_M
Write-Host "done"; Get-Item $ggufQ4 | Format-Table Length, FullName
