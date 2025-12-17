@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo ЗАПУСК УЛУЧШЕННОГО БОТА
echo ========================================
echo.
python advanced_bot.py
pause


