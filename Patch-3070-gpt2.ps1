param([string]$Ip = "192.168.1.34", [string]$User = "expertia", [string]$Pass = "", [string]$HttpBase = "http://192.168.1.42:8000")
if (-not $Pass) { $Pass = $env:EXPERTIA_3070_PASS }
if (-not $Pass) { Write-Host "ERROR: define -Pass o la env EXPERTIA_3070_PASS"; exit 1 }
$sec = ConvertTo-SecureString $Pass -AsPlainText -Force
$cred = New-Object PSCredential($User, $sec)
Write-Host "== 1/3 acceso WinRM $Ip =="
try {
  $h = Invoke-Command -ComputerName $Ip -Credential $cred -ScriptBlock { hostname } -ErrorAction Stop
  Write-Host "OK: $h"
} catch {
  Write-Host "SIN ACCESO: $($_.Exception.Message)"
  Write-Host "En 3070 (admin): irm http://192.168.1.42:8000/enable-remote-3070.ps1 | iex"
  exit 1
}
Write-Host "== 2/3 parche base.py + GGUFs (python, rapido) =="
Invoke-Command -ComputerName $Ip -Credential $cred -ScriptBlock {
  param($HttpBase)
  $py = "C:\training\python311\python.exe"
  Invoke-WebRequest "$HttpBase/patch_gguf_pre.py" -OutFile C:\training\patch_gguf_pre.py -UseBasicParsing
  Invoke-WebRequest "$HttpBase/count_gguf_pre.py" -OutFile C:\training\count_gguf_pre.py -UseBasicParsing
  Write-Host "-- base.py --"
  $base = "C:\training\llama.cpp\conversion\base.py"
  $c = Get-Content $base -Raw
  if ($c.Contains('return "phi-3"')) {
    Copy-Item $base "$base.pre-gpt2.bak" -Force
    $c.Replace('return "phi-3"', 'return "gpt-2"') | Set-Content $base -Encoding utf8
    Write-Host "base.py fallback -> gpt-2"
  } else { Write-Host "base.py ya estaba en gpt-2" }
  foreach ($g in @("C:\training\merged\expertia-math-q4_k_m.gguf", "C:\training\merged\expertia-math-f16.gguf")) {
    if (!(Test-Path $g)) { Write-Host "$g MISSING"; continue }
    Write-Host "-- $g --"
    & $py C:\training\count_gguf_pre.py $g
    & $py C:\training\patch_gguf_pre.py $g
    $tmp = "$g.tmp-gpt2"
    if ((Test-Path $tmp) -and ((Get-Item $tmp).Length -eq (Get-Item $g).Length)) {
      if (!(Test-Path "$g.pre-gpt2.bak")) { Rename-Item $g "$g.pre-gpt2.bak" }
      else { Remove-Item $g -Force }
      Move-Item $tmp $g -Force
      Write-Host "swap ok"
    } else { Write-Host "TMP INVALIDO, no se toca original"; continue }
    & $py C:\training\count_gguf_pre.py $g
  }
} -ArgumentList $HttpBase
Write-Host "== 3/3 done =="
