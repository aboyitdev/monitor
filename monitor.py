import requests
import time
import socket
import os
from datetime import datetime, timedelta

# ================== CONFIG ==================
TELEGRAM_TOKEN = "8108005261:AAEi2TRiGiw4JusJLGfoRvUJaFRvuxdPZTo"
TELEGRAM_CHAT_ID = "1604163126"

WEBSITE_FILE = "C:\\Users\\Talvie IT\\Desktop\\monitor.txt"
LOG_DIR = "C:\\Users\\Talvie IT\\Desktop\\logs"

CHECK_INTERVAL = 15  # giây
DURATION = 60 * 60  # 1 tiếng
RESPONSE_TIME_THRESHOLD = 3000  # ms
KEYWORD_CHECK = "html"  # Nội dung cần có
# ============================================

def load_websites():
    try:
        with open(WEBSITE_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def send_telegram_alert(msg):
    url = f"https://digityze.talvie-it.workers.dev/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"[Telegram ERROR] {e}")

def check_website(url, now, log_lines):
    try:
        domain = url.split("//")[-1].split("/")[0]
        socket.gethostbyname(domain)
    except Exception as e:
        msg = f"[❌ DNS ERROR] {url} không resolve được lúc {now}: {e}"
        print(msg)
        log_lines.append(msg)
        send_telegram_alert(msg)
        return

    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        duration = int((time.time() - start) * 1000)

        if response.status_code != 200:
            msg = f"[❌ DOWN] {url} trả về mã {response.status_code} lúc {now}"
            print(msg)
            log_lines.append(msg)
            send_telegram_alert(msg)
            return

        if duration > RESPONSE_TIME_THRESHOLD:
            msg = f"[⚠️ CHẬM] {url} phản hồi trong {duration}ms lúc {now}"
            print(msg)
            log_lines.append(msg)
            send_telegram_alert(msg)

        if KEYWORD_CHECK.lower() not in response.text.lower():
            msg = f"[⚠️ CONTENT ERROR] {url} không chứa từ khoá '{KEYWORD_CHECK}' lúc {now}"
            print(msg)
            log_lines.append(msg)
            send_telegram_alert(msg)

        msg = f"[✅ OK] {url} - {response.status_code} - {duration}ms"
        print(msg)
        log_lines.append(msg)

    except Exception as e:
        msg = f"[❌ ERROR] Không truy cập được {url} lúc {now}: {e}"
        print(msg)
        log_lines.append(msg)
        send_telegram_alert(msg)

def write_log(log_lines):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(LOG_DIR, f"log_{now_str}.txt")

    with open(log_file, "w", encoding="utf-8") as f:
        for line in log_lines:
            f.write(line + "\n")

def monitor_loop():
    end_time = datetime.now() + timedelta(seconds=DURATION)
    round_count = 0

    while datetime.now() < end_time:
        websites = load_websites()
        now = datetime.now()
        round_count += 1
        log_lines = [f"--- Vòng kiểm tra #{round_count} lúc {now} ({len(websites)} website) ---"]

        for site in websites:
            check_website(site, now, log_lines)

        write_log(log_lines)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_loop()
