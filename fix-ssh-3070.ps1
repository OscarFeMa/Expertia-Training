icacls C:\Users\expertia /inheritance:r /grant 'SYSTEM:(OI)(CI)F' /grant '*S-1-5-32-544:(OI)(CI)F' /grant 'expertia:(OI)(CI)F'
icacls C:\Users\expertia\.ssh /inheritance:r /grant 'SYSTEM:(OI)(CI)F' /grant '*S-1-5-32-544:(OI)(CI)F' /grant 'expertia:(OI)(CI)F'
icacls C:\Users\expertia\.ssh\authorized_keys /inheritance:r /grant 'SYSTEM:F' /grant '*S-1-5-32-544:F' /grant 'expertia:F'
Get-Acl C:\Users\expertia | Format-List
Restart-Service sshd
Get-Service sshd
Write-Host "SSH fixed, test from SOBREMESA: ssh expertia@192.168.1.41 hostname"
