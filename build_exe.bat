@echo off
chcp 65001 >nul
title 打包 — 学生成绩统计工具
echo ============================================
echo   学生成绩统计工具 — 打包 EXE（无控制台）
echo ============================================
echo.

REM 清理旧构建
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "成绩统计工具.spec" del /q "成绩统计工具.spec"

echo [1/2] 正在打包，请稍候（约 1-2 分钟）...
pyinstaller ^
  --onefile ^
  --noconsole ^
  --name "成绩统计工具" ^
  --hidden-import customtkinter ^
  --hidden-import darkdetect ^
  --hidden-import grade_stats ^
  --clean ^
  app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 打包失败！请检查是否已安装依赖：pip install customtkinter pyinstaller
    pause
    exit /b 1
)

echo.
echo [2/2] 打包完成！
echo.
echo ============================================
echo   输出文件：
dir "dist\成绩统计工具.exe" 2>nul
echo ============================================
echo.
echo   双击运行，无黑窗，仅 GUI 窗口！
echo.

pause
