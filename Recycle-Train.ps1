# Recycle-Train.ps1 — reinicio gracioso del entreno vivo (desfragmenta VRAM).
# Uso: tarea programada diaria 05:00 SYSTEM. Si no hay entreno vivo, no hace nada.
# Estrategia: captura la linea de comandos viva, detiene, espera 60s, relanza
# IDENTICOS argumentos (resume automatico desde el ultimo checkpoint).
$Log = "C:\training\logs\recycle.log"
function L($m) { Add-Content $Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" }
L "=== recycle check ==="
$tr = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like '*train_expertia.py*' } | Select-Object -First 1
if (-not $tr) { L "sin entreno vivo, nada que hacer"; exit 0 }
$cmd = [string]$tr.CommandLine
$idx = $cmd.IndexOf('train_expertia.py')
if ($idx -lt 0) { L "cmdline irreconocible, se aborta"; exit 1 }
$args = $cmd.Substring($idx + 'train_expertia.py'.Length).Trim()
$dom = "dom"
if ($cmd -match '--train\s+\S*expertia-([a-z]+)-puro') { $dom = $Matches[1] }
L ("entreno vivo PID=" + $tr.ProcessId + " dom=" + $dom)
try { Stop-Process -Id $tr.ProcessId -Force -ErrorAction Stop; L "detenido" }
catch { L ("no se pudo detener: " + $_.Exception.Message); exit 1 }
Start-Sleep -Seconds 60
$still = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like '*train_expertia*' }
if ($still) { L "sigue vivo tras SIGKILL, se aborta relanzado"; exit 1 }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outLog = "C:\training\logs\train_${dom}_${ts}.log"
$errLog = "C:\training\logs\train_${dom}_${ts}.err.log"
$env:TRAIN_STATUS_FILE = "C:\training\logs\train_status.json"
$env:PYTHONUNBUFFERED = "1"
Start-Process -FilePath "C:\training\python311\python.exe" -ArgumentList ("-u C:\training\train_expertia.py " + $args) -RedirectStandardOutput $outLog -RedirectStandardError $errLog -WindowStyle Hidden
L ("relanzado dom=" + $dom + " log=" + $outLog)
