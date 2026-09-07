# Registers Aya to start automatically when you log into Windows.
# Run this ONCE in an elevated (Administrator) PowerShell window.
#
# Usage:
#   cd C:\Aya\setup
#   .\register_autostart.ps1

$ayaFolder = (Get-Item "$PSScriptRoot\..").FullName
$pythonExe = "$ayaFolder\venv\Scripts\pythonw.exe"   # pythonw = no console window
$mainScript = "$ayaFolder\main.py"

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$mainScript`"" -WorkingDirectory $ayaFolder
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName "AyaAssistant" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "Aya registered to start at logon. Task name: AyaAssistant"
Write-Host "To disable: Unregister-ScheduledTask -TaskName 'AyaAssistant' -Confirm:`$false"
Write-Host "To test right now without rebooting: Start-ScheduledTask -TaskName 'AyaAssistant'"
