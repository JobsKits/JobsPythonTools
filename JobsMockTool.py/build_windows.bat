@echo off
chcp 65001 >nul
setlocal DisableDelayedExpansion
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

call :show_notice || goto :error

echo [JobsMockTool] Create / reuse virtual environment...
python -m venv .venv
if errorlevel 1 goto :error

call .venv\Scripts\activate

python -c "import PySide6.QtWidgets, PySide6.QtWebEngineWidgets, PyInstaller" >nul 2>nul
if errorlevel 1 (
  call :confirm_required_install "Missing project dependencies" || goto :error
  python -m pip install -r requirements.txt || goto :error
  python -c "import PySide6.QtWidgets, PySide6.QtWebEngineWidgets, PyInstaller" || goto :error
)

python "%~dp0scripts\artifact_shortcuts.py" --root "%~dp0." --clear || goto :error
echo [JobsMockTool] Clean old build outputs...
rmdir /s /q build 2>nul
fsutil reparsepoint query "%~dp0dist" >nul 2>nul
if not errorlevel 1 goto :error
rmdir /s /q dist 2>nul
if exist dist goto :error

set "BUILD_STAMP="
for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy.MM.dd HH-mm-ss'"') do set "BUILD_STAMP=%%T"
if not defined BUILD_STAMP goto :error
set "DIST_DIR=%~dp0dist\%BUILD_STAMP%"
echo Build time (YYYY.MM.DD HH-mm-ss): %BUILD_STAMP%

echo [JobsMockTool] Build Windows executable folder...
echo QtWebEngine is large. The generated exe must stay with the "%DIST_DIR%\JobsMockTool" folder.
if not exist "build\pyinstaller-spec" mkdir "build\pyinstaller-spec"
if not exist "build\pyinstaller-spec" goto :error
pyinstaller --noconfirm --clean --specpath "build\pyinstaller-spec" --distpath "%DIST_DIR%" --windowed --onedir --name "JobsMockTool" --collect-all PySide6 app.py
if errorlevel 1 goto :error

echo.
echo ============================================================
echo   Windows executable is here:
echo   %DIST_DIR%\JobsMockTool\JobsMockTool.exe
echo ============================================================
echo.
if not exist "%DIST_DIR%\JobsMockTool\JobsMockTool.exe" goto :error
python "%~dp0scripts\artifact_shortcuts.py" --root "%~dp0." "%DIST_DIR%\JobsMockTool\JobsMockTool.exe" || goto :error
start "" explorer.exe "%DIST_DIR%"
start "" /D "%DIST_DIR%\JobsMockTool" "%DIST_DIR%\JobsMockTool\JobsMockTool.exe"
exit /b 0

:show_notice
cls
echo.
echo ============================================================
echo              JobsMockTool - Windows 打包脚本说明
echo ============================================================
echo.
echo 当前文件：build_windows.bat
echo 用途：把 JobsMockTool 源码打包成 Windows 可执行程序文件夹。
echo Output: dist\YYYY.MM.DD HH-mm-ss\ using local build time, shared by all artifacts.
echo.
echo 【JobsMockTool 是什么】
echo   一个本地 Mock API 桌面工具，用来在没有真实后端、接口不稳定、
echo   或需要模拟异常数据时，快速启动本机假接口服务。
echo.
echo 【它主要能做什么】
echo   - 配置 GET / POST / PUT / PATCH / DELETE 等接口。
echo   - 配置接口路径、端口、响应头、状态码和返回 JSON。
echo   - 支持多接口、条件响应、配置保存 / 加载和内置请求测试。
echo   - 让前端、iOS、Android、脚本或浏览器直接请求本机 Mock 服务。
echo.
echo 【本脚本接下来会做什么】
echo   1. 创建或复用当前目录的 .venv 虚拟环境。
echo   2. 安装 requirements.txt 里的依赖。
echo   3. 清理旧的 build / dist 构建产物。
echo   4. 使用 PyInstaller 打包 Windows 版 JobsMockTool。
echo   5. 输出到：dist\YYYY.MM.DD HH-mm-ss\JobsMockTool\JobsMockTool.exe
echo.
echo 【注意】
echo   - 旧的 build / dist 会被删除，已有构建产物会被覆盖。
echo   - QtWebEngine 体积较大，构建可能较慢，请不要关闭窗口。
echo   - 生成的 exe 需要和 dist\YYYY.MM.DD HH-mm-ss\JobsMockTool 文件夹内其他文件一起使用。
echo.
echo 准备好后按回车开始；按 Ctrl+C 取消。
echo.
powershell -NoLogo -NoProfile -NonInteractive -Command "[Console]::Write('Press Enter to begin JobsMockTool build (EOF cancels): '); $answer = [Console]::In.ReadLine(); if ($null -eq $answer) { exit 1 }; exit 0"
if errorlevel 1 exit /b 1
echo.
exit /b 0

:error
echo.
echo Build failed. Please check the output above.
echo Build clears old dist. On success, reveal output and launch the packaged app.
pause
exit /b 1

:confirm_required_install
rem ReadLine 保留空格，并把 EOF 当成取消。
powershell -NoProfile -Command "[Console]::Write('%~1 (Enter to install; any character to cancel): '); $answer = [Console]::ReadLine(); if ($null -eq $answer -or $answer.Length -gt 0) { exit 1 }; exit 0"
if errorlevel 1 (
  echo Dependency installation cancelled. Stopping current task.
  exit /b 1
)
exit /b 0
