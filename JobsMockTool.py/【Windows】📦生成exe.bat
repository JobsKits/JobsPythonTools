@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%JobsMockTool"

call :show_notice

if not exist "%PROJECT_ROOT%\app.py" (
  echo [ERROR] Missing project file: %PROJECT_ROOT%\app.py
  pause
  exit /b 1
)
cd /d "%PROJECT_ROOT%"

echo [JobsMockTool] Create / reuse virtual environment...
python -m venv .venv
if errorlevel 1 goto :error

call .venv\Scripts\activate

echo [JobsMockTool] Install dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :error

echo [JobsMockTool] Clean old build outputs...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [JobsMockTool] Build Windows executable folder...
echo QtWebEngine is large. The generated exe must stay with %PROJECT_ROOT%\dist\JobsMockTool folder.
pyinstaller --noconfirm --clean --windowed --onedir --name "JobsMockTool" --collect-all PySide6 app.py
if errorlevel 1 goto :error

echo.
echo ============================================================
echo   Windows executable is here:
echo   %PROJECT_ROOT%\dist\JobsMockTool\JobsMockTool.exe
echo ============================================================
echo.
pause
exit /b 0

:show_notice
cls
echo.
echo ============================================================
echo              JobsMockTool - Windows 打包脚本说明
echo ============================================================
echo.
echo 当前文件：%~f0
echo 用途：把 JobsMockTool 源码打包成 Windows 可执行程序文件夹。
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
echo   1. 创建或复用 JobsMockTool\.venv 虚拟环境。
echo   2. 安装 JobsMockTool\requirements.txt 里的依赖。
echo   3. 清理 JobsMockTool\build / JobsMockTool\dist 构建产物。
echo   4. 使用 PyInstaller 打包 Windows 版 JobsMockTool。
echo   5. 输出到：JobsMockTool\dist\JobsMockTool\JobsMockTool.exe
echo.
echo 【注意】
echo   - 内层 JobsMockTool\build / JobsMockTool\dist 会被删除，已有构建产物会被覆盖。
echo   - QtWebEngine 体积较大，构建可能较慢，请不要关闭窗口。
echo   - 生成的 exe 需要和 JobsMockTool\dist\JobsMockTool 文件夹内其他文件一起使用。
echo.
echo 准备好后按回车开始；按 Ctrl+C 取消。
echo.
set /p __jobsmock_start=^>^>^> 按回车开始构建 JobsMockTool Windows 版：
echo.
exit /b 0

:error
echo.
echo Build failed. Please check the output above.
pause
exit /b 1
