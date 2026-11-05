param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
)

$ErrorActionPreference = "Stop"
$BuildStamp = Get-Date -Format "yyyy.MM.dd HH-mm-ss"
$OutputDir = Join-Path (Split-Path -Parent $ProjectRoot) "dist\$BuildStamp"
Set-Location $ProjectRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "未找到 python，请先安装 Python 后再构建 IPA环境体检.exe"
}

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip 更新失败，退出码 $LASTEXITCODE" }
python -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 安装失败，退出码 $LASTEXITCODE" }
python -m PyInstaller `
    --distpath "$OutputDir" `
    --onefile `
    --console `
    --name "IPA环境体检" `
    --paths "$ProjectRoot" `
    "$ProjectRoot\doctor\doctor_entry.py"
if ($LASTEXITCODE -ne 0) { throw "IPA环境体检构建失败，退出码 $LASTEXITCODE" }

$OutputFile = Join-Path $OutputDir 'IPA环境体检.exe'
if (-not (Test-Path -LiteralPath $OutputFile -PathType Leaf) -or (Get-Item -LiteralPath $OutputFile).Length -eq 0) {
    throw "未生成有效构建产物：$OutputFile"
}
Write-Host "构建完成：$OutputFile"
