#!/usr/bin/env pwsh
# Empacota o codigo + dependencias em lambda_local.zip para deploy no LocalStack.
# Uso: .\scripts\build_local_lambda.ps1

$ROOT = Split-Path $PSScriptRoot -Parent
$BUILD = "$ROOT\build_lambda"
$ZIP   = "$ROOT\lambda_local.zip"

Write-Host "Limpando build anterior..."
Remove-Item -Recurse -Force $BUILD -ErrorAction SilentlyContinue
Remove-Item -Force $ZIP -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $BUILD | Out-Null

Write-Host "Instalando dependencias..."
pip install -r "$ROOT\requirements.txt" --target $BUILD --quiet --upgrade

Write-Host "Copiando codigo..."
Copy-Item "$ROOT\lambda_handler.py" $BUILD
Copy-Item "$ROOT\src"    $BUILD -Recurse
Copy-Item "$ROOT\config" $BUILD -Recurse

Write-Host "Criando zip..."
Compress-Archive -Path "$BUILD\*" -DestinationPath $ZIP -Force

Remove-Item -Recurse -Force $BUILD
$size = [math]::Round((Get-Item $ZIP).Length / 1MB, 2)
Write-Host "Criado: lambda_local.zip ($size MB)"
