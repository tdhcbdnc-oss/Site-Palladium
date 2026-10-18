#!/usr/bin/env python3
# Пинг IndexNow: сообщает Яндексу и Bing, что страницы сайта изменились.
# Запуск после выкладки:  python3 build/indexnow.py
# Список адресов берётся из sitemap.xml в корне сайта.

import json, re, urllib.request, urllib.error, pathlib, sys

HOST = "palladium.com.ru"
KEY = "4f09da33b91242458960eef9a7806525"
SITEMAP = pathlib.Path(__file__).resolve().parent.parent / "sitemap.xml"
URLS = re.findall(r"<loc>(.*?)</loc>", SITEMAP.read_text(encoding="utf-8"))
ENDPOINTS = ["https://yandex.com/indexnow", "https://api.indexnow.org/indexnow"]

def ping():
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt",
                       "urlList": URLS}).encode()
    ok = True
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                print(f"{ep}: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            # 200/202 — принято; 403 — ключ ещё не выложен
            print(f"{ep}: HTTP {e.code} {e.read().decode()[:200]}")
            ok = ok and e.code in (200, 202)
        except Exception as e:
            print(f"{ep}: {e}")
            ok = False
    return ok

if __name__ == "__main__":
    print(len(URLS), "адресов")
    sys.exit(0 if ping() else 1)
