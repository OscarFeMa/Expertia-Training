# gpu_boot.ps1 — fija el punto dulce 1580MHz + persistencia en cada arranque.
# Uso: tarea SYSTEM AtStartup. Sin esto el driver arranca en boost libre (~1950MHz).
$Log = "C:\training\logs\gpu_boot.log"
function L($m) { Add-Content $Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" }
L "=== gpu boot tune ==="
try {
  $r = nvidia-smi -pm 1 2>&1 | Out-String
  L ("persistencia: " + $r.Trim())
  $r = nvidia-smi --lock-gpu-clocks=1580 2>&1 | Out-String
  L ("lock 1580: " + $r.Trim())
  Start-Sleep -Seconds 5
  $v = ((nvidia-smi --query-gpu=clocks.sm --format=csv 2>$null) | Where-Object { $_ -match '\d' } | Select-Object -Last 1)
  L ("relojes: " + $v)
} catch { L ("FALLO: " + $_.Exception.Message) }
