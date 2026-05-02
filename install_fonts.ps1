# Download and install Inter and Fira Code fonts
$ErrorActionPreference = 'Stop'

$fontDir = "$env:TEMP\quantia_fonts"
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null

# Download Inter
Write-Host "Downloading Inter..."
$interUrl = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
$interZip = "$fontDir\Inter.zip"
Invoke-WebRequest -Uri $interUrl -OutFile $interZip
Expand-Archive -Path $interZip -DestinationPath "$fontDir\Inter" -Force

# Download Fira Code
Write-Host "Downloading Fira Code..."
$firaUrl = "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip"
$firaZip = "$fontDir\FiraCode.zip"
Invoke-WebRequest -Uri $firaUrl -OutFile $firaZip
Expand-Archive -Path $firaZip -DestinationPath "$fontDir\FiraCode" -Force

# Install fonts (copy to user fonts folder)
$userFonts = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $userFonts | Out-Null

$shell = New-Object -ComObject Shell.Application
$fontsFolder = $shell.Namespace(0x14)  # Windows Fonts folder

$installed = 0

# Install Inter - look for variable font or static TTFs
$interFiles = Get-ChildItem -Path "$fontDir\Inter" -Filter "*.ttf" -Recurse | Where-Object { $_.Name -match 'Inter' -and $_.Name -notmatch 'Italic' }
foreach ($f in $interFiles) {
    Write-Host "  Installing $($f.Name)..."
    Copy-Item $f.FullName -Destination "$userFonts\$($f.Name)" -Force
    # Register in registry
    New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "$($f.BaseName) (TrueType)" -Value "$userFonts\$($f.Name)" -PropertyType String -Force | Out-Null
    $installed++
}

# Install Fira Code
$firaFiles = Get-ChildItem -Path "$fontDir\FiraCode" -Filter "*.ttf" -Recurse | Where-Object { $_.Name -match 'FiraCode' }
foreach ($f in $firaFiles) {
    Write-Host "  Installing $($f.Name)..."
    Copy-Item $f.FullName -Destination "$userFonts\$($f.Name)" -Force
    New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "$($f.BaseName) (TrueType)" -Value "$userFonts\$($f.Name)" -PropertyType String -Force | Out-Null
    $installed++
}

Write-Host "`nDone! Installed $installed font files."
Write-Host "Note: You may need to restart Quantia for fonts to take effect."

# Cleanup
Remove-Item -Recurse -Force $fontDir
