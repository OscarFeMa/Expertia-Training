param([string]$IpHint="192.168.1.46")
$Log="F:\expertia\logs\auto_post.log"
function L($m){ Add-Content $Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" }
$Inc="D:\proyectos\expertia\training\incoming_3070\train_status.json"
if(!(Test-Path $Inc)){ L "sin espejo"; exit 0 }
try{ $js=Get-Content $Inc -Raw -Encoding utf8 | ConvertFrom-Json }catch{ L "json roto"; exit 0 }
if($js.phase -ne "done" -or $js.step -lt 8436){
  L "no done (training $($js.step))"
  exit 0
}
L "TRIGGER done $($js.step) -> espera post 3070 (merge/eval/gguf por Watch-Train)"
$Pass3070 = $env:EXPERTIA_3070_PASS
if (-not $Pass3070) { L "ERROR: env EXPERTIA_3070_PASS no definida"; exit 1 }
$sec=ConvertTo-SecureString $Pass3070 -AsPlainText -Force; $cred=New-Object PSCredential("expertia",$sec)
$ip=@(arp -a 2>$null | Select-String "E0-0A-F6-9E-CB-01" | ForEach-Object{ if($_ -match "(192\.168\.1\.\d+)"){ $Matches[1] } }) | Select-Object -First 1
if(-not $ip){ $ip=$IpHint }
$ready=$false
$deadline=(Get-Date).AddHours(3)
while((Get-Date) -lt $deadline){
  try{
    $done=Invoke-Command -ComputerName $ip -Credential $cred -ScriptBlock{
      (Test-Path C:\training\merged\expertia-electronics-q4_k_m.gguf) -and (Test-Path C:\training\logs\eval_electronics_adapter.json)
    } -ErrorAction Stop
    if($done){ L "3070 post listo (Q4+eval)"; $ready=$true; break }
  }catch{}
  Start-Sleep -Seconds 60
}
if(-not $ready){ L "WARN timeout 3h esperando Q4+eval del 3070, abortando (sin transfer falso)"; exit 1 }
L "transfer y HF..."
try{
  net use "\\$ip\C$" /user:expertia $Pass3070 2>$null | Out-Null
  robocopy "\\$ip\C$\training\merged" "D:\training\merged" "expertia-electronics-q4_k_m.gguf" /J 2>&1 | Out-Null
  robocopy "\\$ip\C$\training\merged" "D:\training\merged" "expertia-electronics-f16.gguf" /J 2>&1 | Out-Null
  robocopy "\\$ip\C$\training\merged\expertia-electronics-fp16" "D:\training\merged\expertia-electronics-fp16" /MIR /J 2>&1 | Out-Null
  robocopy "\\$ip\C$\training\logs" "D:\training\logs_3070" "eval_electronics_base.json" "eval_electronics_adapter.json" /J 2>&1 | Out-Null
  net use "\\$ip\C$" /delete 2>$null | Out-Null
  $q4=Test-Path "D:\training\merged\expertia-electronics-q4_k_m.gguf"
  $f16=Test-Path "D:\training\merged\expertia-electronics-f16.gguf"
  if($q4 -and $f16){ L "transfer OK Q4+F16+fp16+evals" }
  else{ L "ERROR transfer incompleto Q4=$q4 F16=$f16"; exit 1 }
}catch{ L "WARN transfer: $($_.Exception.Message)"; exit 1 }
$OllamaBin="C:\Users\usuario\AppData\Local\Programs\Ollama\ollama.exe"
try{
  Set-Content "D:\training\Modelfile-ExpertiaElectronics-Q4F" -Value @"
FROM F:\expertia\training-disk\merged\expertia-electronics-q4_k_m.gguf
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
PARAMETER num_predict 1000
PARAMETER stop "<|end|>"
PARAMETER stop "<|endoftext|>"
PARAMETER stop "<|endofprompt|>"
SYSTEM "Eres ExpertiaElectronics, electronico puro. Responde solo con definicion formal, parametros y formula cuando aplique. Sin opinion web."
"@ -Encoding utf8
  & $OllamaBin create expertia-electronics -f "D:\training\Modelfile-ExpertiaElectronics-Q4F" 2>&1 | Out-Null
  $listed=& $OllamaBin list 2>&1 | Out-String
  if($listed -match "expertia-electronics"){ L "ollama create expertia-electronics OK" }
  else{ L "ERROR ollama create sin modelo en list"; exit 1 }
}catch{ L "WARN ollama: $($_.Exception.Message)"; exit 1 }
try{
  $env:HF_HUB_ENABLE_HF_TRANSFER="1"
  Start-Process -FilePath "C:\Users\usuario\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -ArgumentList "D:\proyectos\expertia\training\hf_cards\upload_hf.py" -WindowStyle Hidden
  L "HF upload lanzado"
}catch{ L "WARN HF: $($_.Exception.Message)" }
try{ Disable-ScheduledTask -TaskName "AutoPostElectronics" | Out-Null; L "watcher desactivado (una vez)" }catch{}
L "CADENA POST ELECTRONICS COMPLETADA (canario manual pendiente)"
