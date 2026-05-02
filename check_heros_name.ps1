[System.Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null
$pfc = New-Object System.Drawing.Text.PrivateFontCollection
$fontPath = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\texgyreheros-regular.otf"
if (Test-Path $fontPath) {
    $pfc.AddFontFile($fontPath)
    $pfc.Families | Select-Object -ExpandProperty Name
} else {
    Write-Host "File not found: $fontPath"
}
