#!/usr/bin/env python3
# Пинг IndexNow: мгновенно сообщает Яндексу и Bing об изменившихся страницах.
# Запуск после каждого деплоя с изменением контента:  python3 build/indexnow.py
#
# Ключ лежит файлом <KEY>.txt в корне сайта (требование протокола — поисковик
# проверяет владение доменом, скачивая этот файл). Кабинет Вебмастера не нужен.

import json, urllib.request, pathlib, sys

HOST = "palladium.com.ru"
KEY = "4f09da33b91242458960eef9a7806525"
URLS = [
    f"https://{HOST}/",
    f"https://{HOST}/cases.html",
    f"https://{HOST}/products.html",
]

ENDPOINTS = ["https://yandex.com/indexnow", "https://api.indexnow.org/indexnow"]

def ping():
    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": URLS,
    }).encode()
    ok = True
    for ep in ENDPOINTS:
        req = urllib.request.Request(
            ep, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                print(f"{ep}: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            # 200/202 — принято; 4xx — разбираться (403 = ключ ещё не задеплоен)
            print(f"{ep}: HTTP {e.code} {e.read().decode()[:200]}")
            ok = ok and e.code in (200, 202)
        except Exception as e:
            print(f"{ep}: {e}")
            ok = False
    return ok

if __name__ == "__main__":
    sys.exit(0 if ping() else 1)
