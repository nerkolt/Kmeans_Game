param(
    [ValidateSet("onedir","onefile","installer")]
    [string]$Mode = "onedir",
    [string]$Name = "KmeansGame"
)

$ErrorActionPreference = "Stop"

Write-Host "Building $Name ($Mode)..." -ForegroundColor Cyan

python -m pip install --upgrade pip | Out-Host
python -m pip install pyinstaller pillow | Out-Host

# Entry script
$Entry = "Scripts\Kmeans_Game_Debug.py"

# Build icon from Assets/logo.png for Windows EXE/installer.
$IconOut = "build\logo.ico"
$IconSrc = "Assets\logo.png"
if (-not (Test-Path $IconSrc)) { $IconSrc = "Assets\logo_try.png" }
if (Test-Path $IconSrc) {
    python tools\make_icon.py $IconSrc $IconOut | Out-Host
} else {
    Write-Host "Warning: no icon source found (Assets/logo.png or Assets/logo_try.png). Building without icon." -ForegroundColor Yellow
    $IconOut = $null
}

if ($Mode -eq "onefile") {
    if ($IconOut) {
        python -m PyInstaller --noconfirm --clean --windowed --onefile --name $Name --icon $IconOut --paths Scripts $Entry | Out-Host
    } else {
        python -m PyInstaller --noconfirm --clean --windowed --onefile --name $Name --paths Scripts $Entry | Out-Host
    }
    Write-Host "Done. Output: dist\$Name.exe" -ForegroundColor Green
} elseif ($Mode -eq "installer") {
    if ($IconOut) {
        python -m PyInstaller --noconfirm --clean --windowed --name $Name --icon $IconOut --paths Scripts $Entry | Out-Host
    } else {
        python -m PyInstaller --noconfirm --clean --windowed --name $Name --paths Scripts $Entry | Out-Host
    }
    Write-Host "Built app folder. Output: dist\$Name\$Name.exe" -ForegroundColor Green

    $Iscc = Get-Command iscc -ErrorAction SilentlyContinue
    if (-not $Iscc) {
        Write-Host "Inno Setup compiler (iscc) not found." -ForegroundColor Yellow
        Write-Host "Install Inno Setup, then run: iscc installer.iss" -ForegroundColor Yellow
        return
    }

    iscc installer.iss | Out-Host
    Write-Host "Done. Output: dist-installer\$Name-Setup-*.exe" -ForegroundColor Green
} else {
    if ($IconOut) {
        python -m PyInstaller --noconfirm --clean --windowed --name $Name --icon $IconOut --paths Scripts $Entry | Out-Host
    } else {
        python -m PyInstaller --noconfirm --clean --windowed --name $Name --paths Scripts $Entry | Out-Host
    }
    Write-Host "Done. Output: dist\$Name\$Name.exe" -ForegroundColor Green
}


