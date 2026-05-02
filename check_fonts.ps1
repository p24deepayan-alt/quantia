[System.Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null
$fonts = (New-Object System.Drawing.Text.InstalledFontCollection).Families | Select-Object -ExpandProperty Name
$check = @('Inter','Fira Code','Cascadia Code','Cascadia Mono','Helvetica')
foreach ($f in $check) {
    if ($fonts -contains $f) {
        Write-Host "$f : INSTALLED"
    } else {
        Write-Host "$f : MISSING"
    }
}
