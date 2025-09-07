@echo off
rem %~dp0 会获取当前bat文件所在的目录
call "%~dp0venv\scripts\activate.bat"

echo "Launching the app..."
python.exe "%~dp0app.py"
echo "The app has finished."
pause