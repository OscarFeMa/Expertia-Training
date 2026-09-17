param([int]$StagingSec=30, [int]$WatchSec=1800)
$Log="C:\training\logs\clock_tune.log"
function L($m){ Add-Content $Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" }
$StateFile="C:\training\logs\clock_tune_state.txt"
$Stages=@(1320,1440,1580)
$Idx=0; $Current=1200
if(Test-Path $StateFile){ try{ $j=Get-Content $StateFile -Raw | ConvertFrom-Json; $Idx=$j.nextIdx; $Current=$j.current }catch{} }
$Adapter="C:\training\adapters\expertia-electronics-r16"
$LastCkpt=(Get-ChildItem $Adapter -Directory -Filter "checkpoint-*" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1 -ExpandProperty Name)
L "autotune start current=$Current nextIdx=$Idx last=$LastCkpt"
while($true){
  Start-Sleep -Seconds 60
  $NewCkpt=(Get-ChildItem $Adapter -Directory -Filter "checkpoint-*" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1 -ExpandProperty Name)
  if(-not $NewCkpt -or $NewCkpt -eq $LastCkpt){ continue }
  L "nuevo checkpoint $NewCkpt (antes $LastCkpt)"
  $LastCkpt=$NewCkpt
  Start-Sleep -Seconds $StagingSec
  if($Idx -ge $Stages.Count){ L "todos probados, fin"; break }
  $Next=$Stages[$Idx]
  L "probando ${Next}MHz"
  nvidia-smi --lock-gpu-clocks=$Next 2>&1 | Out-String | ForEach-Object{ L "nvidia-smi: $_" }
  # vigila 30 min
  $Start=Get-Date; $EventsBefore=(Get-EventLog -LogName System -After $Start -ErrorAction SilentlyContinue | Where-Object{ $_.Source -like "*nvlddmkm*" } | Measure-Object).Count
  Start-Sleep -Seconds $WatchSec
  $EventsAfter=(Get-EventLog -LogName System -After $Start -ErrorAction SilentlyContinue | Where-Object{ $_.Source -like "*nvlddmkm*" } | Measure-Object).Count
  $NewEvents=$EventsAfter - $EventsBefore
  $Throttle=(nvidia-smi -q 2>&1 | Select-String "Throttle" | Out-String)
  $HasThrottle=$Throttle -match "Active"
  if($NewEvents -gt 0 -or $HasThrottle){
    $Back=[int]($Current*0.95)
    if($Back -lt 1200){ $Back=1200 }
    L "FALLO ${Next}MHz events=$NewEvents throttle=$HasThrottle -> retrocede a ${Back}MHz"
    nvidia-smi --lock-gpu-clocks=$Back 2>&1 | Out-String | ForEach-Object{ L "rollback: $_" }
    @{current=$Back; nextIdx=$Stages.Count; last=$LastCkpt} | ConvertTo-Json | Set-Content $StateFile -Encoding utf8
    break
  } else {
    L "OK ${Next}MHz"
    $Current=$Next; $Idx++
    @{current=$Current; nextIdx=$Idx; last=$LastCkpt} | ConvertTo-Json | Set-Content $StateFile -Encoding utf8
    if($Idx -ge $Stages.Count){ L "punto dulce final $Current"; break }
  }
}
