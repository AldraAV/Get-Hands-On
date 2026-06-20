<#
.SYNOPSIS
    Script de compilación para MeterMano a .exe usando PyInstaller.
.PARAMETER Portable
    Si se especifica, compila en modo --onefile: un único .exe portable.
    Sin este parámetro, compila en --onedir (más rápido de lanzar, pero requiere carpeta _internal).
.EXAMPLE
    .\build.ps1             # Modo carpeta (default, rápido al lanzar)
    .\build.ps1 -Portable  # Modo un solo .exe (portable, lento al lanzar)
#>
param(
    [switch]$Portable
)

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
if ($Portable) {
    Write-Host "[!] Modo: ONEFILE (un solo .exe portable)" -ForegroundColor Magenta
    Write-Host "[!] Puede tardar mas en compilar (+5 min) pero el resultado es un unico archivo." -ForegroundColor Yellow
    pyinstaller MeterMano-onefile.spec --noconfirm --clean
} else {
    Write-Host "[i] Modo: ONEDIR (carpeta con _internal, lanzamiento rapido)" -ForegroundColor Cyan
    pyinstaller MeterMano.spec --noconfirm --clean
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Compilacion Exitosa" -ForegroundColor DarkGreen
    if ($Portable) {
        Write-Host "Ejecutable listo en: .\dist\MeterMano.exe" -ForegroundColor Yellow
        Write-Host "Puedes copiar ese .exe a cualquier lado. Se autoextrae al lanzar." -ForegroundColor Gray
    } else {
        Write-Host "Carpeta lista en: .\dist\MeterMano\" -ForegroundColor Yellow
        Write-Host "Copia la carpeta COMPLETA (no solo el .exe) para distribuir." -ForegroundColor Gray
    }
} else {
    Write-Host "[!] Error de compilacion." -ForegroundColor Red
}
Write-Host "============================" -ForegroundColor Cyan
