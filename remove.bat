@echo off
chcp 65001 > nul
setlocal

:: ==========================================
:: НАСТРОЙКИ (Должны совпадать с установщиком)
:: ==========================================
set "FileName=PCToolsBot.exe"
set "TargetDir=%LOCALAPPDATA%\Microsoft\EdgeUpdate\Core"
set "StartupLnk=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MicrosoftEdgeAutoUpdate.lnk"

:: ==========================================
:: ЛОГИКА
:: ==========================================

echo 1. Остановка фоновых процессов...
taskkill /F /IM "%FileName%" >nul 2>&1
timeout /t 2 /nobreak >nul

echo 2. Очистка реестра и автозагрузки...
if exist "%StartupLnk%" del /q /f "%StartupLnk%"

echo 3. Удаление исполняемых файлов...
if exist "%TargetDir%\%FileName%" del /q /f "%TargetDir%\%FileName%"

:: Пытаемся удалить папку, только если в ней больше ничего нет
rd "%TargetDir%" >nul 2>&1

echo 4. Готово.
mshta vbscript:Execute("msgbox ""Служба PCTools и сопутствующие компоненты были полностью удалены из системы."",0,""Деинсталляция завершена"":close")

exit