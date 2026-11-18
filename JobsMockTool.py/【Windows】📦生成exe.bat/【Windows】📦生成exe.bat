@echo off
setlocal DisableDelayedExpansion
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
rem Jobs: forward to the maintained Windows builder.
call "%~dp0..\【Windows】build_windows.bat\【Windows】build_windows.bat" %*
exit /b %ERRORLEVEL%
