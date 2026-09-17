Add-Type -Path "C:\training\lhm\LibreHardwareMonitorLib.dll"
$pc = New-Object LibreHardwareMonitor.Hardware.Computer
$pc.IsCpuEnabled = $true
$pc.IsGpuEnabled = $true
$pc.IsMemoryEnabled = $false
$pc.IsMotherboardEnabled = $true
$pc.IsControllerEnabled = $false
$pc.IsNetworkEnabled = $false
$pc.IsStorageEnabled = $false
$pc.Open()
foreach ($hw in $pc.Hardware) {
  $hw.Update()
  foreach ($s in $hw.Sensors) {
    if ($s.SensorType -in @("Temperature", "Fan", "Load", "Power") -and $s.Value -ne $null) {
      "{0} | {1} | {2} = {3}" -f $hw.Name, $hw.HardwareType, $s.Name, [math]::Round($s.Value, 1)
    }
  }
  foreach ($sub in $hw.SubHardware) {
    $sub.Update()
    foreach ($s in $sub.Sensors) {
      if ($s.SensorType -in @("Temperature", "Fan") -and $s.Value -ne $null) {
        "{0} / {1} | {2} = {3}" -f $hw.Name, $sub.Name, $s.Name, [math]::Round($s.Value, 1)
      }
    }
  }
}
$pc.Close()
