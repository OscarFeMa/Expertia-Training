param(
  [string]$Ip = "192.168.1.34",
  [string]$User = "expertia",
  [string]$Pass = "",
  [string]$Dataset = "expertia-physics-puro.jsonl",
  [string]$Adapter = "expertia-physics-r16",
  [int]$SeqLen = 1024,
  [string]$HttpBase = "http://192.168.1.42:8000"
)
if (-not $Pass) { $Pass = $env:EXPERTIA_3070_PASS }
if (-not $Pass) { Write-Host "ERROR: define -Pass o la env EXPERTIA_3070_PASS"; exit 1 }
$sec = ConvertTo-SecureString $Pass -AsPlainText -Force
$cred = New-Object PSCredential($User, $sec)
function Remote($sb, $extra) {
  if ($null -eq $extra) { Invoke-Command -ComputerName $Ip -Credential $cred -ScriptBlock $sb -ErrorAction Stop }
  else { Invoke-Command -ComputerName $Ip -Credential $cred -ScriptBlock $sb -ArgumentList $extra -ErrorAction Stop }
}
try { $h = Remote({ hostname }); Write-Host "3070 OK: $h" } catch {
  Write-Host "SIN ACCESO a ${Ip}: $($_.Exception.Message)"; exit 1
}
$cmdLines = @(
  "@echo off",
  "setlocal",
  "set TRAIN_STATUS_FILE=C:\training\logs\train_status.json",
  "set PYTHONUNBUFFERED=1",
  "C:\training\python311\python.exe -u C:\training\train_expertia.py --model C:\training\base\phi-4-mini-reasoning --train C:\training\datasets\$Dataset --out C:\training\adapters\$Adapter --offload C:\training\offload --epochs 3 --seq-len $SeqLen --batch 1 --accum 16 --bf16 --save-steps 200 > C:\training\logs\train_physics.log 2> C:\training\logs\train_physics.err.log"
)
$cmdText = $cmdLines -join "`r`n"
Set-Content "D:\proyectos\expertia\training\Run-Physics.cmd" -Value $cmdText -Encoding ascii
$dl = {
  param($HttpBase)
  try { Invoke-WebRequest "$HttpBase/Run-Physics.cmd" -OutFile C:\training\Run-Physics.cmd -UseBasicParsing } catch {}
  $alive = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine -like "*train_expertia*"
  }
  if ($alive) { Write-Host "YA HAY ENTRENO VIVO, no se duplica"; return }
  # One-shot sin cita-trampa: programa a +2min con /Z y borra tras verificar arranque.
  # (/SC ONCE /ST 23:59 + /Run dejaba la cita viva: el /Run no la consume y re-dispara a las 23:59.)
  $st = (Get-Date).AddMinutes(2).ToString('HH:mm')
  schtasks /Create /TN "ExpertiaTrainPhysics" /TR "C:\training\Run-Physics.cmd" /SC ONCE /ST $st /RU SYSTEM /F
  schtasks /Run /TN "ExpertiaTrainPhysics"
  Start-Sleep -Seconds 60
  $up = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*train_expertia*" }
  if ($up) { schtasks /Delete /TN "ExpertiaTrainPhysics" /F; Write-Host "tarea lanzada y eliminada (one-shot consumido)" }
  else { Write-Host "AVISO: sin proceso tras 60s, tarea conservada para inspeccion" }
}
Remote $dl $HttpBase
Start-Sleep -Seconds 75
$st = Remote({
  @{ py = @(Get-Process python -ErrorAction SilentlyContinue).Count
     status = (Get-Content C:\training\logs\train_status.json -Raw -ErrorAction SilentlyContinue)
     gpu = (nvidia-smi --query-gpu=utilization.gpu --format=csv 2>$null | Select-Object -Last 1) }
})
Write-Host "python vivos: $($st.py) | gpu: $($st.gpu) | status: $($st.status)"
Write-Host "HECHO. Cierra esta sesion: el entreno sobrevive solo (tarea SYSTEM)."
