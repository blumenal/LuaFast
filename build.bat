@echo off
setlocal

REM Always run from the script directory.
cd /d "%~dp0"

REM ---------------------------------------------------------------------------
REM Configurable build options
REM   GENERATOR  - CMake generator (default: Visual Studio 17 2022)
REM   ARCH       - Architecture for multi-config generators (default: x64)
REM   CONFIGS    - Configurations to build, space-separated (default: Release Debug)
REM ---------------------------------------------------------------------------

REM Forçar uso do Visual Studio em vez do Ninja
set "GENERATOR=Visual Studio 17 2022"
set "ARCH=x64"
set "CONFIGS=Release Debug"

echo [INFO] Configuring project with generator: %GENERATOR%
echo "%GENERATOR%" | findstr /I /C:"Visual Studio" >nul
if not errorlevel 1 (
    cmake -S src -B build -G "%GENERATOR%" -A %ARCH%
) else (
    cmake -S src -B build -G "%GENERATOR%"
)
if errorlevel 1 goto :fail

for %%C in (%CONFIGS%) do (
    echo [INFO] Building %%C...
    cmake --build build --config %%C
    if errorlevel 1 goto :fail
)

echo [OK] Build completed successfully.
exit /b 0

:fail
echo [ERROR] Build failed.
exit /b 1