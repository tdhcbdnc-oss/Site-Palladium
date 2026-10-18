#!/usr/bin/env python3
# Сборка сайта palladium.com.ru из исходников в src/.
#
#   python3 build.py            → dist/  (рабочая версия: Метрика, абсолютные ссылки)
#   python3 build.py --preview  → preview/ (для просмотра: без Метрики, ссылки на index.html)
#
# Страница — файл src/pages/<имя>.html. Первая строка — JSON с мета-данными
# в HTML-комментарии, дальше — содержимое <main>. Шапка, подвал, блок контактов,
# <head>, разметка для поисковиков и Метрика добавляются здесь, одинаково для всех.
#
# Подстановки в тексте страниц:
#   {{icon:имя}}   — встроенная SVG-иконка из ICONS
#   {{wa:текст}}   — ссылка на WhatsApp с готовым сообщением
#   {{href:файл}}  — ссылка на страницу сайта (в превью и на проде по-разному)
#   {{contacts}}   — общий блок «С чего начнём» с контактами
#
# FAQ для поисковиков собирается из видимых <details> внутри .faq — текст
# в разметке и на странице совпадает дословно, как требуют Яндекс и Google.

import json, re, shutil, sys, pathlib, datetime, html as H, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("preview" if PREVIEW else "dist")

BASE = "https://palladium.com.ru"
TODAY = datetime.date.today().isoformat()
METRIKA_ID = "111244444"
YANDEX_VERIFICATION = "547ee5d5867898fe"
GOOGLE_VERIFICATION = None
INDEXNOW_KEY = "4f09da33b91242458960eef9a7806525"

PHONE = "+7 949 020-93-08"
PHONE_RAW = "+79490209308"
WA_NUM = "79490209308"
WA_TEXT = "Здравствуйте! Хочу записаться на 30-минутный разбор."
TG = "ShirinTimur"
EMAIL = "info@palladium.com.ru"

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
 "%3Crect width='64' height='64' rx='14' fill='%230f131c'/%3E"
 "%3Ctext x='32' y='45' font-family='Helvetica,Arial,sans-serif' font-size='38' font-weight='700'"
 " fill='%2334d58a' text-anchor='middle'%3EP%3C/text%3E%3C/svg%3E")

# Меню — одинаковое на всех страницах.
NAV = [("videoanalitika.html", "Palladium Vision"), ("sotrudniki.html", "Цифровые сотрудники"), ("uslugi.html", "Услуги"),
       ("cases.html", "Кейсы"), ("o-kompanii.html", "О компании")]

# Порядок и приоритет в карте сайта.
SITEMAP = [("index.html", "1.0"), ("videoanalitika.html", "0.9"), ("sotrudniki.html", "0.9"), ("uslugi.html", "0.9"),
           ("chat-boty.html", "0.8"), ("ai-audit.html", "0.8"), ("cases.html", "0.8"),
           ("o-kompanii.html", "0.7")]

# Старые адреса, которые остались в поиске и закладках: страница-переадресация.
REDIRECTS = {"products.html": ("uslugi.html", "Услуги")}

# ---------------------------------------------------------------- иконки
def _svg(body):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + body + '</svg>')

ICONS = {k: _svg(v) for k, v in {
 "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
 "wave": '<path d="M3 12h2M7 8v8M11 5v14M15 9v6M19 7v10M21 12h0"/>',
 "camera": '<path d="M15 10l5-3v10l-5-3"/><rect x="3" y="7" width="12" height="10" rx="2"/>',
 "db": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
 "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.8c1.8.7 3 2.5 3.5 5.2"/>',
 "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
 "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
 "gov": '<path d="M3 21h18M5 21V10M19 21V10M9 21V10M15 21V10M2 10l10-6 10 6z"/>',
 "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
 "send": '<path d="M21 3L3 10.5l7 3 3 7z"/><path d="M10 13.5L21 3"/>',
 "chat": '<path d="M20 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z"/>',
 "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
 "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
 "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
 "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
 "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
 "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 "coffee": '<path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM17 10h1.5a2.5 2.5 0 0 1 0 5H17M8 3v3M12 3v3"/>',
 "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h0"/>',
 "shield": '<path d="M12 3l8 3v6c0 4.5-3.4 8.4-8 9-4.6-.6-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
 "server": '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h0M7 16.5h0"/>',
 "face": '<circle cx="12" cy="12" r="9"/><path d="M9 10h0M15 10h0M8.5 15c1 1.2 2.2 1.8 3.5 1.8s2.5-.6 3.5-1.8"/>',
 "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
 "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
 "film": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
 "flow": '<rect x="3" y="3" width="6" height="6" rx="1.5"/><rect x="15" y="15" width="6" height="6" rx="1.5"/><path d="M9 6h4a3 3 0 0 1 3 3v6"/>',
 "layers": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
 "book": '<path d="M4 4h6a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H4zM20 4h-5a2 2 0 0 0-2 2"/><path d="M20 4v15h-5"/>',
 "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>',
 "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
 "wa": '<path d="M4 20l1.3-4A8 8 0 1 1 8 19z"/><path d="M9 9.5c.3 2.4 2.2 4.6 5 5.3l1.2-1.3-1.8-1-1 .8c-.9-.4-1.6-1.1-2-2l.8-1-1-1.8z"/>',
 "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
 "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
}.items()}

# ---------------------------------------------------------------- ссылки
def href(page):
    if page in ("", "index.html", "/"):
        return "index.html" if PREVIEW else "/"
    if page.startswith("index.html#"):
        return page if PREVIEW else "/" + page[len("index.html"):]
    return page if PREVIEW else "/" + page

def wa(text=WA_TEXT):
    return f"https://wa.me/{WA_NUM}?text=" + urllib.parse.quote(text)

# ---------------------------------------------------------------- JSON-LD
ORG = {
 "@context": "https://schema.org", "@type": "Organization",
 "@id": BASE + "/#org", "name": "Palladium", "url": BASE + "/",
 "logo": BASE + "/og-image.jpg", "slogan": "Внешний AI-отдел",
 "description": "Внешний AI-отдел: внедряем цифровых сотрудников и AI-системы, "
                "которые остаются в собственности клиента — на его серверах и в его аккаунтах.",
 "email": EMAIL, "telephone": PHONE_RAW,
 "address": {"@type": "PostalAddress", "addressLocality": "Донецк", "addressCountry": "RU"},
 "areaServed": "RU",
 "contactPoint": {"@type": "ContactPoint", "telephone": PHONE_RAW,
                  "contactType": "sales", "availableLanguage": ["Russian"]},
 "sameAs": ["https://t.me/" + TG],
}
WEBSITE = {"@context": "https://schema.org", "@type": "WebSite", "@id": BASE + "/#website",
           "url": BASE + "/", "name": "Palladium", "inLanguage": "ru",
           "publisher": {"@id": BASE + "/#org"}}

def crumbs_ld(trail):
    items = [{"@type": "ListItem", "position": 1, "name": "Главная", "item": BASE + "/"}]
    for i, (name, page) in enumerate(trail):
        items.append({"@type": "ListItem", "position": i + 2, "name": name, "item": BASE + "/" + page})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}

def service_ld(name, desc, page):
    return {"@context": "https://schema.org", "@type": "Service", "name": name,
            "description": desc, "url": BASE + "/" + page,
            "provider": {"@id": BASE + "/#org"}, "areaServed": "RU", "availableLanguage": "ru"}

def strip_tags(s):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", s))).strip()

def faq_from(body):
    pairs = []
    for block in re.findall(r'<div class="faq">(.*?)</div>\s*<!--/faq-->', body, re.S):
        for q, a in re.findall(r"<summary>(.*?)</summary>(.*?)</details>", block, re.S):
            pairs.append((strip_tags(q), strip_tags(a)))
    if not pairs:
        return None
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}

def services_catalog(body):
    # Каталог услуг для поисковиков — из карточек .svc на странице «Услуги».
    items = []
    for name, desc in re.findall(r'<article class="card svc"[^>]*>.*?<h3>(.*?)</h3>\s*<p>(.*?)</p>', body, re.S):
        items.append({"@type": "Offer", "itemOffered": {"@type": "Service", "name": strip_tags(name),
                      "description": strip_tags(desc), "provider": {"@id": BASE + "/#org"}}})
    return {"@context": "https://schema.org", "@type": "OfferCatalog", "name": "Услуги Palladium",
            "url": BASE + "/uslugi.html", "provider": {"@id": BASE + "/#org"}, "itemListElement": items}

# ---------------------------------------------------------------- куски страницы
def metrika():
    return ("""<!-- Yandex.Metrika counter -->
<script type="text/javascript">
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=""" + METRIKA_ID + """', 'ym');

    ym(""" + METRIKA_ID + """, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/""" + METRIKA_ID + """" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->
""")

# Цели Метрики по кликам на контакты — те же, что стояли на посадочных.
GOALS = ("""<script>document.addEventListener('click',function(e){
var n=e.target;while(n&&n.nodeType===1&&n.tagName!=='A')n=n.parentNode;
if(!n||n.nodeType!==1)return;var h=n.getAttribute('href')||'';
var g=h.indexOf('tel:')===0?'click_phone':h.indexOf('wa.me')>=0?'click_whatsapp'
:h.indexOf('t.me')>=0?'click_telegram':h.indexOf('mailto:')===0?'click_email':null;
if(g&&typeof ym==='function')ym(""" + METRIKA_ID + """,'reachGoal',g);},true);</script>""")

# Кнопка меню на мобильном.
MENU_JS = """<script>(function(){var b=document.querySelector('.burger'),n=document.getElementById('nav');
if(!b||!n)return;b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)});
n.addEventListener('click',function(e){if(e.target.tagName==='A'){n.classList.remove('open');b.setAttribute('aria-expanded','false')}});})();</script>"""

def head(meta, lds, asset):
    title, desc, page = meta["title"], meta["description"], meta["page"]
    canon = BASE + ("/" if page == "index.html" else "/" + page)
    og_title = meta.get("og_title", title)
    t = [
     '<meta charset="utf-8">',
     '<meta name="viewport" content="width=device-width, initial-scale=1">',
     f"<title>{H.escape(title, quote=False)}</title>",
     f'<meta name="description" content="{H.escape(desc)}">',
     '<meta name="theme-color" content="#0f131c">',
     f'<link rel="canonical" href="{canon}">',
     f'<link rel="icon" href="{FAVICON}">',
     f'<link rel="icon" type="image/x-icon" sizes="32x32" href="{asset}favicon.ico">',
     f'<link rel="apple-touch-icon" href="{asset}apple-touch-icon.png">',
     f'<link rel="preload" href="{asset}assets/fonts/unbounded-cyrillic-700-normal.woff2" as="font" type="font/woff2" crossorigin>',
     f'<link rel="preload" href="{asset}assets/fonts/inter-cyrillic-400-normal.woff2" as="font" type="font/woff2" crossorigin>',
     f'<link rel="stylesheet" href="{asset}assets/site.css">',
     f'<meta property="og:title" content="{H.escape(og_title)}">',
     f'<meta property="og:description" content="{H.escape(desc)}">',
     f'<meta property="og:url" content="{canon}">',
     '<meta property="og:type" content="website">',
     '<meta property="og:locale" content="ru_RU">',
     '<meta property="og:site_name" content="Palladium">',
     f'<meta property="og:image" content="{BASE}/og-image.jpg">',
     '<meta property="og:image:width" content="1200">',
     '<meta property="og:image:height" content="630">',
     '<meta property="og:image:alt" content="Palladium — внешний AI-отдел">',
     '<meta name="twitter:card" content="summary_large_image">',
     f'<meta name="twitter:image" content="{BASE}/og-image.jpg">',
    ]
    if meta.get("noindex"):
        t.append('<meta name="robots" content="noindex">')
    if YANDEX_VERIFICATION:
        t.append(f'<meta name="yandex-verification" content="{YANDEX_VERIFICATION}">')
    if GOOGLE_VERIFICATION:
        t.append(f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION}">')
    for ld in lds:
        t.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>")
    return "\n".join(t)

def header(active):
    links = "\n".join(
        f'      <a href="{href(p)}"' + (' aria-current="page"' if p == active else "") + f">{label}</a>"
        for p, label in NAV)
    return f"""<a class="skip" href="#main">К содержимому</a>
<header class="top">
  <div class="wrap">
    <a class="logo" href="{href('index.html')}" aria-label="Palladium — на главную"><b>PALLADIUM</b></a>
    <nav class="nav" id="nav" aria-label="Основное меню">
{links}
      <a class="btn" href="{href('index.html#kontakty')}">Обсудить задачу</a>
    </nav>
    <a class="btn sm" href="{href('index.html#kontakty') if active != 'index.html' else '#kontakty'}">Обсудить задачу</a>
    <button class="burger" type="button" aria-controls="nav" aria-expanded="false" aria-label="Меню">{ICONS['menu']}</button>
  </div>
</header>"""

def contacts_block(title="С чего начнём?", text=None):
    text = text or ("30-минутный разбор вашей ситуации — бесплатно и без обязательств. "
                    "Расскажете, как устроен бизнес, — покажем, где AI даст эффект быстрее всего. "
                    "А если вам пока рано, так и скажем.")
    return f"""<section class="contact" id="kontakty">
  <div class="wrap contact-grid">
    <div>
      <p class="eyebrow">Контакты</p>
      <h2>{title}</h2>
      <p class="lead">{text}</p>
      <div class="cta-row mt">
        <a class="btn" href="{wa()}" target="_blank" rel="noopener">{ICONS['wa']} Записаться на разбор</a>
      </div>
    </div>
    <div class="ways">
      <a href="{wa()}" target="_blank" rel="noopener">{ICONS['wa']}<span><small>WhatsApp</small><b>Написать в WhatsApp</b></span></a>
      <a href="https://t.me/{TG}" target="_blank" rel="noopener">{ICONS['send']}<span><small>Telegram</small><b>@{TG}</b></span></a>
      <a href="tel:{PHONE_RAW}">{ICONS['phone']}<span><small>Телефон</small><b>{PHONE}</b></span></a>
      <a href="mailto:{EMAIL}">{ICONS['mail']}<span><small>Почта</small><b>{EMAIL}</b></span></a>
    </div>
  </div>
</section>"""

def footer():
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <a class="logo" href="{href('index.html')}"><b>PALLADIUM</b></a>
        <p class="mt" style="margin-top:14px;max-width:34ch">Внешний AI-отдел: цифровые сотрудники и AI-системы, которые остаются вашими.</p>
      </div>
      <div><h4>Разделы</h4><ul>
        <li><a href="{href('videoanalitika.html')}">Palladium Vision</a></li>
        <li><a href="{href('sotrudniki.html')}">Цифровые сотрудники</a></li>
        <li><a href="{href('uslugi.html')}">Услуги</a></li>
        <li><a href="{href('cases.html')}">Кейсы</a></li>
        <li><a href="{href('o-kompanii.html')}">О компании</a></li>
      </ul></div>
      <div><h4>С чего начать</h4><ul>
        <li><a href="{href('ai-audit.html')}">AI-аудит</a></li>
        <li><a href="{href('chat-boty.html')}">AI-чат-боты</a></li>
        <li><a href="{href('videoanalitika.html#start')}">Пилот Palladium Vision</a></li>
        <li><a href="{href('sotrudniki.html#start')}">Пилот цифрового сотрудника</a></li>
      </ul></div>
      <div><h4>Связаться</h4><ul>
        <li><a href="tel:{PHONE_RAW}">{PHONE}</a></li>
        <li><a href="{wa()}" target="_blank" rel="noopener">WhatsApp</a></li>
        <li><a href="https://t.me/{TG}" target="_blank" rel="noopener">Telegram @{TG}</a></li>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
      </ul></div>
    </div>
    <div class="copy"><span>© 2026 Palladium · Донецк</span><span>Системы, которые остаются вашими</span></div>
  </div>
</footer>"""

# ---------------------------------------------------------------- сборка
def render(src_path):
    raw = src_path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(\{.*?\})-->\s*", raw, re.S)
    assert m, f"{src_path.name}: нет JSON-шапки"
    meta = json.loads(m.group(1))
    body = raw[m.end():]
    page = src_path.name
    meta["page"] = page
    asset = "/" if (meta.get("abs_assets") and not PREVIEW) else ""

    body = body.replace("{{contacts}}", contacts_block(**meta.get("contacts", {})) if meta.get("contacts") is not False else "")
    body = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda x: ICONS[x.group(1)], body)
    body = re.sub(r"\{\{wa:(.*?)\}\}", lambda x: H.escape(wa(x.group(1))), body)
    body = re.sub(r"\{\{wa\}\}", lambda x: H.escape(wa()), body)
    body = re.sub(r"\{\{href:(.*?)\}\}", lambda x: href(x.group(1)), body)
    body = body.replace("{{asset}}", asset)
    left = re.findall(r"\{\{[^}]*\}\}", body)
    assert not left, f"{page}: неизвестные подстановки {left}"

    lds = []
    if page == "index.html":
        lds += [ORG, WEBSITE]
    if meta.get("crumbs"):
        lds.append(crumbs_ld([tuple(c) for c in meta["crumbs"]]))
    if meta.get("service"):
        s = meta["service"]
        lds.append(service_ld(s["name"], s["description"], page))
    if page == "uslugi.html":
        lds.append(services_catalog(body))
    faq = faq_from(body)
    if faq:
        lds.append(faq)

    tail = MENU_JS
    if not PREVIEW and not meta.get("noindex"):
        tail += "\n" + metrika() + GOALS
    elif not PREVIEW:
        tail += "\n" + metrika()

    doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
{head(meta, lds, asset)}
</head>
<body>
{header(meta.get('nav', page))}
<main id="main">
{body.strip()}
</main>
{footer()}
{tail}
</body>
</html>
"""
    (OUT / page).write_text(doc, encoding="utf-8")
    return page, meta["title"], len(doc.encode())

def redirect_page(old, new, label):
    target = href(new)
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>{label} — Palladium</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{BASE}/{new}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(target)}+location.hash)</script>
</head><body style="background:#0f131c;color:#eef1f6;font:16px/1.6 system-ui,sans-serif;padding:40px">
<p>Страница переехала: <a style="color:#34d58a" href="{target}">{label}</a>.</p>
</body></html>
"""

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(SRC / "assets", OUT / "assets")
    for f in (SRC / "static").iterdir():
        if f.is_file():
            shutil.copy(f, OUT / f.name)
    if not PREVIEW:
        (OUT / ".nojekyll").write_text("")
        (OUT / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY)

    for p in sorted((SRC / "pages").glob("*.html")):
        page, title, size = render(p)
        print(f"{page:18s} {size//1024:4d} КБ  {title[:70]}")

    for old, (new, label) in REDIRECTS.items():
        (OUT / old).write_text(redirect_page(old, new, label), encoding="utf-8")
        print(f"{old:18s}   → {new}")

    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /build/\n\nSitemap: " + BASE + "/sitemap.xml\n")
    items = "\n".join(
        f"  <url>\n    <loc>{BASE}{'/' if p == 'index.html' else '/' + p}</loc>\n    <lastmod>{TODAY}</lastmod>\n"
        f"    <changefreq>monthly</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        for p, pr in SITEMAP)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + items + "\n</urlset>\n")

    # Проверка внутренних ссылок: каждая ссылка на страницу сайта должна вести на существующий файл.
    bad = []
    for f in OUT.glob("*.html"):
        for link in re.findall(r'href="([^"#:?]+\.html)', f.read_text(encoding="utf-8")):
            if not (OUT / link.lstrip("/")).exists():
                bad.append((f.name, link))
    for f, link in bad:
        print(f"  ! битая ссылка в {f}: {link}")
    print("готово:", OUT)

if __name__ == "__main__":
    main()
