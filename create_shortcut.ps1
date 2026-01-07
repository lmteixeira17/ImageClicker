# Script para criar atalho do ImageClicker no Desktop
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$appPath = Join-Path $scriptPath "app_qt.py"
$iconPath = Join-Path $scriptPath "final_icon.ico"

# Encontra pythonw.exe
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    $pythonw = "C:\Python313\pythonw.exe"
}

# Obtém o desktop do usuário
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "ImageClicker.lnk"

# Cria o atalho
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$appPath`""
$shortcut.WorkingDirectory = $scriptPath
$shortcut.IconLocation = $iconPath
$shortcut.Description = "ImageClicker - Automacao de cliques"
$shortcut.Save()

Write-Host "Atalho criado em: $shortcutPath"
Write-Host "Python: $pythonw"
Write-Host "App: $appPath"
