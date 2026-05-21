@echo off
REM ============================================================
REM  Tank Battle PVP - Build EXE (Windows, 1-click)
REM ============================================================
REM  - Tu phat hien Python
REM  - Cai pygame + pyinstaller neu thieu
REM  - Build TankBattle.exe (onefile, windowed, kem sprites + nhac)
REM  - Output: dist\TankBattle.exe
REM ============================================================

setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title Build TankBattle.exe

REM ---- Pick Python ----
set "PY="
where py >nul 2>nul && set "PY=py -3"
if "!PY!"=="" ( where python >nul 2>nul && set "PY=python" )
if "!PY!"=="" (
    echo [LOI] Khong tim thay Python. Cai Python 3.10+ tai python.org va tich "Add to PATH".
    pause
    exit /b 1
)

echo Dung Python: !PY!
!PY! --version
echo.

REM ---- Install deps ----
echo [1/3] Kiem tra pygame + pyinstaller...
!PY! -m pip install --upgrade --quiet pip
!PY! -m pip install --upgrade --quiet pygame pyinstaller
if !ERRORLEVEL! NEQ 0 (
    echo [LOI] Cai dependencies that bai. Kiem tra mang.
    pause
    exit /b 1
)

REM ---- Clean ----
echo [2/3] Don dep build cu...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TankBattle.spec del /q TankBattle.spec

REM ---- Build ----
echo [3/3] Dang build TankBattle.exe (1-3 phut)...
!PY! -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name TankBattle ^
    --add-data "sprites.py;." ^
    --add-data "nhacnen.mp3;." ^
    --add-data "TACH.mp3;." ^
    --add-data "IMG;IMG" ^
    tank_game.py

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [LOI] Build that bai. Xem log ben tren.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  DONE! File: dist\TankBattle.exe
echo ============================================================
echo Mo dist\ ?  (Y/N)
choice /c YN /n /m ""
if !ERRORLEVEL!==1 explorer dist
endlocal
exit /b 0
