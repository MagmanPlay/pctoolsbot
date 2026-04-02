import os
import re
import shutil
import subprocess
import concurrent.futures
from pathlib import Path

# ==========================================
# КОНФИГУРАЦИЯ ФАБРИКИ
# ==========================================
SOURCE_FILE = "PCToolsBot.py"
TOKENS_FILE = "tokens.txt"
WIREPROXY_FILE = "wireproxy.exe"
ICON_FILE = "icon.ico"
OUTPUT_DIR = "bots"
TEMP_DIR = "build_temp"

def check_requirements():
    """Проверяет наличие всех необходимых файлов перед стартом"""
    missing = []
    for f in [SOURCE_FILE, TOKENS_FILE, WIREPROXY_FILE]:
        if not os.path.exists(f):
            missing.append(f)
    if missing:
        print(f"❌ ОШИБКА: Не найдены файлы: {', '.join(missing)}")
        return False
    return True

def build_bot(target):
    user_id, token, alias = target
    
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        code = f.read()

    code = re.sub(r"^my_id\s*=\s*\d+", f"my_id = {user_id}", code, flags=re.MULTILINE)
    code = re.sub(r"^bot_token\s*=\s*['\"].*?['\"]", f"bot_token = '{token}'", code, flags=re.MULTILINE)

    temp_script_name = f"temp_{alias}.py"
    with open(temp_script_name, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"⏳ [{alias}] Начинаю сборку...")

    dist_path = os.path.abspath(os.path.join(OUTPUT_DIR, alias))
    work_path = os.path.abspath(os.path.join(TEMP_DIR, alias))
    
   # ❗️ ГЕНЕРИРУЕМ АБСОЛЮТНЫЕ ПУТИ ❗️
    abs_wireproxy = os.path.abspath(WIREPROXY_FILE)
    abs_script = os.path.abspath(temp_script_name)
    abs_icon = os.path.abspath(ICON_FILE)

    cmd = [
        "pyinstaller",
        "-w",
        "-F",
        "--hidden-import", "requests_negotiate_sspi",
        "--hidden-import", "pysocks",
        "--add-binary", f"{abs_wireproxy};.", 
        "--distpath", dist_path,
        "--workpath", work_path,
        "--specpath", work_path,
        "-n", "msedge"
    ]

    # Если файл иконки лежит рядом со скриптом, вшиваем его!
    if os.path.exists(abs_icon):
        cmd.extend(["--icon", abs_icon])

    # Имя скрипта всегда должно быть последним аргументом
    cmd.append(abs_script)

    try:
        result_run = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        exe_path = os.path.join(dist_path, "msedge.exe")
        if os.path.exists(exe_path):
            result = f"✅ [{alias}] УСПЕХ! Путь: {exe_path}"
            success = True
        else:
            result = f"❌ [{alias}] ОШИБКА: Файл не найден.\nЛог:\n{result_run.stdout[-500:]}"
            success = False
            
    except subprocess.CalledProcessError as e:
        error_tail = e.stderr[-1000:] if e.stderr else "Пустой ответ от PyInstaller"
        result = f"❌ [{alias}] КРАШ PYINSTALLER:\n{error_tail}"
        success = False
        exe_path = None
    finally:
        if os.path.exists(temp_script_name):
            os.remove(temp_script_name)

    return success, result, exe_path

def main():
    print("🏭 Добро пожаловать на Фабрику Ботов!\n" + "="*40)
    
    if not check_requirements():
        return

    # Читаем токены
    targets = []
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            parts = line.split(":")
            # Формат ID:TOKEN:ALIAS содержит минимум 3 части (токен сам может содержать двоеточие)
            if len(parts) >= 3:
                user_id = parts[0]
                alias = parts[-1]
                # Склеиваем токен обратно, если внутри него было двоеточие
                token = ":".join(parts[1:-1]) 
                targets.append((user_id, token, alias))
            else:
                print(f"⚠️ Ошибка формата в строке {line_num}: {line}")

    if not targets:
        print("❌ Файл tokens.txt пуст или имеет неверный формат.")
        return

    print(f"📋 Найдено целей для сборки: {len(targets)}")
    
    # Создаем базовые папки
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Запускаем параллельную сборку
    # ВНИМАНИЕ: Если ПК слабый, max_workers можно уменьшить до 2 или 1
    max_threads = min(len(targets), os.cpu_count() or 4)
    print(f"🚀 Запускаю параллельную сборку (Потоков: {max_threads}). Пожалуйста, ждите...\n")

    successful_builds = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Отправляем задачи в пул
        future_to_alias = {executor.submit(build_bot, target): target[2] for target in targets}
        
        for future in concurrent.futures.as_completed(future_to_alias):
            success, message, path = future.result()
            print(message)
            if success:
                successful_builds += 1

    # Заметаем следы (чистим тяжелые папки build)
    print("\n🧹 Очистка временных файлов сборки...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)

    print("="*40)
    print(f"🎉 Сборка завершена! Успешно: {successful_builds}/{len(targets)}")
    print(f"📁 Все боты лежат в папке: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()