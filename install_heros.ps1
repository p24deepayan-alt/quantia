# Download and install TeX Gyre Heros (Helvetica clone)
$ErrorActionPreference = 'Stop'

$fontDir = "$env:TEMP\quantia_fonts_heros"
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null

Write-Host "Downloading TeX Gyre Heros..."
# Direct download link for TeX Gyre Heros from FontSquirrel
$herosUrl = "https://www.fontsquirrel.com/fonts/download/tex-gyre-heros"
$herosZip = "$fontDir\heros.zip"

Invoke-WebRequest -Uri $herosUrl -OutFile $herosZip
Expand-Archive -Path $herosZip -DestinationPath "$fontDir\Heros" -Force

# Install fonts (copy to user fonts folder)
$userFonts = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $userFonts | Out-Null

$shell = New-Object -ComObject Shell.Application
$fontsFolder = $shell.Namespace(0x14)  # Windows Fonts folder

$installed = 0

$herosFiles = Get-ChildItem -Path "$fontDir\Heros" -Filter "*.otf" -Recurse
foreach ($f in $herosFiles) {
    Write-Host "  Installing $($f.Name)..."
    Copy-Item $f.FullName -Destination "$userFonts\$($f.Name)" -Force
    # Register in registry
    New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "$($f.BaseName) (OpenType)" -Value "$userFonts\$($f.Name)" -PropertyType String -Force | Out-Null
    $installed++
}

Write-Host "`nDone! Installed $installed font files."

# Clean up
Remove-Item -Recurse -Force $fontDir
