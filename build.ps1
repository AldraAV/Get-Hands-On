<#
.SYNOPSIS
    Script de compilación para MeterMano a .exe usando PyInstaller.
#>

$ErrorActionPreference = "Stop"

Write-Host "============================" -ForegroundColor Cyan
Write-Host "Empaquetando MeterMano" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# Comprobar PyInstaller
if (-Not (Get-Command "pyinstaller" -ErrorAction SilentlyContinue)) {
    Write-Host "[!] PyInstaller no encontrado. Instalando..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error instalando PyInstaller." -ForegroundColor Red
        exit 1
    }
}

# Limpieza
Write-Host "[*] Limpiando carpetas build y dist..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Compilacion
Write-Host "[*] Compilando con PyInstaller..." -ForegroundColor Green
pyinstaller MeterMano.spec --noconfirm --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Compilacion Exitosa" -ForegroundColor DarkGreen
    Write-Host "Carpeta lista en: .\dist\MeterMano\" -ForegroundColor Yellow
} else {
    Write-Host "[!] Error de compilacion." -ForegroundColor Red
}
Write-Host "============================" -ForegroundColor Cyan
