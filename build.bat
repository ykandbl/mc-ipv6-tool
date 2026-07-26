@echo off
setlocal
cd /d "%~dp0"

for /f "delims=" %%V in ('python -c "import sys;sys.path.insert(0,'src');from app_version import APP_VERSION;print(APP_VERSION)"') do set "APP_VERSION=%%V"
if not defined APP_VERSION goto :error

echo [1/3] Installing build dependencies...
python -m pip install -r requirements-dev.txt || goto :error

echo [2/3] Running tests...
python -m pytest -q || goto :error

echo [3/3] Building IPv6Tool-v%APP_VERSION%.exe...
python -m PyInstaller build.spec --clean --noconfirm || goto :error

echo.
echo Build completed: dist\IPv6Tool-v%APP_VERSION%.exe
exit /b 0

:error
echo.
echo Build failed. Review the output above.
exit /b 1
