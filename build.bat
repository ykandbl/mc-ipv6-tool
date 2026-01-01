@echo off
echo ========================================
echo IPv6 地址工具 - 打包脚本
echo ========================================

echo.
echo 正在安装依赖...
pip install -r requirements.txt

echo.
echo 正在打包...
pyinstaller build.spec --clean

echo.
echo ========================================
echo 打包完成！
echo 可执行文件位于: dist\IPv6Tool.exe
echo ========================================
pause
