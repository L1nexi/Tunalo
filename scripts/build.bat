@echo off
setlocal
cd /d "%~dp0.." || exit /b 1
set "PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo Virtual environment not found: %PYTHON%
    exit /b 1
)
set "FRONTEND_APP_DIR=frontend"
set "FRONTEND_DIST_DIR=%FRONTEND_APP_DIR%\dist"
set "BUILD_EXIT_CODE=0"

echo ==========================================
echo      Tunalo Build Script
echo ==========================================

echo [1/5] Installing dependencies...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [2/5] Building frontend...
pushd "%FRONTEND_APP_DIR%"
if errorlevel 1 goto :failed
call npm ci
if errorlevel 1 goto :failed
call npm run build
set "BUILD_EXIT_CODE=%errorlevel%"
popd
if not "%BUILD_EXIT_CODE%"=="0" goto :finish

echo [3/5] Cleaning up previous builds...
if exist "%CD%\build" rmdir /s /q "%CD%\build"
if exist "%CD%\build" goto :failed
if exist "%CD%\dist" rmdir /s /q "%CD%\dist"
if exist "%CD%\dist" goto :failed

echo [4/5] Running PyInstaller...
"%PYTHON%" -m PyInstaller --noconfirm --noconsole --onefile --name "Tunalo" ^
    --icon "%CD%\packaging\AppIcon.ico" ^
    --paths "%CD%\src" ^
    --add-data "%CD%\%FRONTEND_DIST_DIR%;%FRONTEND_DIST_DIR%" ^
    --add-data "%CD%\packaging\AppIcon.ico;." ^
    --add-data "%CD%\packaging\PausedIcon.ico;." ^
    --specpath build ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=psutil ^
    --hidden-import=win32gui ^
    --hidden-import=win32con ^
    --hidden-import=win32api ^
    --exclude-module=numpy ^
    --exclude-module=matplotlib ^
    --clean ^
    main.py

if errorlevel 1 goto :failed

echo [5/5] Preparing distribution folder...
"%PYTHON%" scripts\release.py stage --dist "%CD%\dist"
if errorlevel 1 goto :failed

echo ==========================================
echo      Build Complete!
echo      Executable is in: dist\Tunalo.exe
echo ==========================================
goto :finish

:failed
set "BUILD_EXIT_CODE=%errorlevel%"
if "%BUILD_EXIT_CODE%"=="0" set "BUILD_EXIT_CODE=1"
echo Build failed.

:finish
if /i not "%~1"=="--no-pause" pause
exit /b %BUILD_EXIT_CODE%
