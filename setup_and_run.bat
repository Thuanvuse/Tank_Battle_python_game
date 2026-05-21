@echo off
REM ============================================================
REM  Tank Battle PVP - Setup & Run (Windows)
REM ============================================================
REM  - Checks for Python (uses py launcher first, falls back to python)
REM  - Installs/upgrades pygame quietly if needed
REM  - Launches the game
REM ============================================================

setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

title Tank Battle PVP - Setup ^& Run
echo ============================================================
echo   TANK BATTLE PVP - Setup ^& Run
echo ============================================================
echo.

REM ---- Pick a Python launcher ----
set "PY="
where py >nul 2>nul
if !ERRORLEVEL!==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if !ERRORLEVEL!==0 (
        set "PY=python"
    )
)

if "!PY!"=="" (
    echo [LOI] Khong tim thay Python tren may.
    echo Vui long cai Python 3.10+ tai: https://www.python.org/downloads/
    echo Khi cai nho tich "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [1/3] Dang dung Python:  !PY!
!PY! --version
echo.

REM ---- Make sure pip is available ----
!PY! -m pip --version >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo [2/3] pip chua co - cai dat...
    !PY! -m ensurepip --upgrade
    if !ERRORLEVEL! NEQ 0 (
        echo [LOI] Khong the cai pip. Hay cai lai Python.
        pause
        exit /b 1
    )
)

REM ---- Install/upgrade pygame ----
echo [2/3] Kiem tra pygame...
!PY! -c "import pygame, sys; sys.exit(0)" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo     -^> pygame chua co, dang cai dat...
    !PY! -m pip install --upgrade pip >nul 2>nul
    !PY! -m pip install pygame
    if !ERRORLEVEL! NEQ 0 (
        echo [LOI] Cai pygame that bai. Vui long kiem tra ket noi mang.
        pause
        exit /b 1
    )
) else (
    echo     -^> pygame da co san.
)
echo.

REM ---- Optional: Setuptools downgrade to silence pkg_resources warning ----
!PY! -c "import setuptools, sys; v=int(setuptools.__version__.split('.')[0]); sys.exit(0 if v<81 else 1)" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo     -^> Setuptools moi (^>=81) co warning pkg_resources, ha xuong ban tuong thich...
    !PY! -m pip install "setuptools<81" --quiet >nul 2>nul
)

REM ---- Launch the game ----
echo [3/3] Khoi dong Tank Battle...
echo.
!PY! "%~dp0tank_game.py"
set "GAME_RC=!ERRORLEVEL!"

echo.
if !GAME_RC! NEQ 0 (
    echo [LUU Y] Game thoat voi ma loi !GAME_RC!.
) else (
    echo [DONE] Game ket thuc binh thuong.
)
echo.
pause
endlocal
exit /b !GAME_RC!
