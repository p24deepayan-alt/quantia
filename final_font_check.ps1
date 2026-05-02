[System.Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null
$fonts = (New-Object System.Drawing.Text.InstalledFontCollection).Families | Select-Object -ExpandProperty Name

$requiredFonts = @(
    'Segoe UI',
    'Arial',
    'Times New Roman',
    'Consolas',
    'Cambria',
    'Georgia',
    'DejaVu Sans',
    'TeXGyreHeros',
    'Inter',
    'Fira Code',
    'Cascadia Code'
)

Write-Host "--- Quantia Font Audit ---"
$allInstalled = $true
foreach ($f in $requiredFonts) {
    if ($fonts -contains $f) {
        Write-Host "[OK] $f" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $f" -ForegroundColor Red
        $allInstalled = $false
    }
}
Write-Host "--------------------------"
if ($allInstalled) {
    Write-Host "SUCCESS: All required fonts are installed." -ForegroundColor Green
} else {
    Write-Host "WARNING: Some fonts are missing and will use fallbacks." -ForegroundColor Yellow
}
