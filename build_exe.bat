@echo off
echo ===============================
echo  Chess App EXE Build Script
echo ===============================
echo.

REM -----------------------------
REM Configuration
REM -----------------------------
set APP_NAME=InteractiveChessBoard
set ENTRY_FILE=main.py

REM -----------------------------
REM Clean Old Builds
REM -----------------------------
echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q %APP_NAME%.spec 2>nul

REM -----------------------------
REM Build EXE
REM -----------------------------
echo Building %APP_NAME%.exe...
echo.

pyinstaller ^
  --onefile ^
  --name %APP_NAME% ^
  --add-data "assets/icons;assets/icons" ^
  --add-data "assets/pieces;assets/pieces" ^
  --collect-submodules pygame ^
  --collect-binaries pygame ^
  %ENTRY_FILE%

REM -----------------------------
REM Done
REM -----------------------------
echo.
echo ===============================
echo  Build Complete
echo ===============================
echo Output:
echo dist\%APP_NAME%.exe
echo.
pause
