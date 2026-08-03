#!/usr/bin/env python3
# Сборка сайта palladium.com.ru из offline-экспортов Claude Design.
#
# Запуск из корня репозитория:  python3 build/build.py
# Экспорты берутся из iCloud Drive (куда их кладёт выгрузка из Claude Design),
# результат пишется прямо в корень репозитория. После сборки: git diff, коммит, пуш.
#
# Что делает сверх переименования ссылок (каждый блок помечен в коде):
#   1. Статический <head>: title, description, canonical, og/twitter, favicon —
#      боты мессенджеров и поисковиков не исполняют JS, без этого превью ссылки пустое.
#   2. JSON-LD (Organization, WebSite, FAQPage, OfferCatalog, BreadcrumbList) —
#      статически в <head> и повторно через скрипт-хранитель после свапа документа.
#   3. SEO-пререндер: семантический HTML всей страницы из build/prerender/*.html
#      вставляется в body. Рантайм при монтировании заменяет documentElement целиком,
#      поэтому пререндер видят только роботы без JS и посетители с выключенным JS.
#   4. Правки консистентности текста (TEXT_FIXES) — до исправления в канвасе Claude Design.
#   5. Скрипт-хранитель: мета-теги, подсказка прокрутки, гашение заглушек, JSON-LD,
#      карточка WhatsApp в контактах (вместо самоссылки «Сайт»).
#   6. robots.txt и sitemap.xml с текущей датой.
#   7. Яндекс.Метрика — вставляется, когда METRIKA_ID задан.

import json, pathlib, re, datetime, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"
OUT = REPO
PRERENDER_DIR = pathlib.Path(__file__).resolve().parent / "prerender"

BASE = "https://palladium.com.ru"
TODAY = datetime.date.today().isoformat()

# Номер счётчика Яндекс.Метрики (стоит с 31.07.2026).
METRIKA_ID = "111244444"

# Коды подтверждения прав на сайт. Когда Тимур заведёт сайт в кабинетах,
# вписать содержимое content их мета-тегов — сборка добавит теги в <head>.
# Яндекс.Вебмастер: <meta name="yandex-verification" content="...">
# Google Search Console: <meta name="google-site-verification" content="...">
YANDEX_VERIFICATION = "547ee5d5867898fe"
GOOGLE_VERIFICATION = None

# Ключ IndexNow (файл <KEY>.txt лежит в корне сайта, пинг — build/indexnow.py).
INDEXNOW_KEY = "4f09da33b91242458960eef9a7806525"

WA_NUM = "79490209308"
WA_TEXT = "Здравствуйте! Хочу записаться на 30-минутный разбор."

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
 "%3Crect width='64' height='64' rx='14' fill='%23050a1e'/%3E"
 "%3Ctext x='32' y='45' font-family='Helvetica,Arial,sans-serif' font-size='38' font-weight='700'"
 " fill='%235980a6' text-anchor='middle'%3EP%3C/text%3E%3C/svg%3E")

# Для каждой страницы два заголовка: title — поисковый (запрос в начале, читает
# робот и выдача), og_title — брендовый (читает человек в превью мессенджера).
# Описания несут и запросные слова, и оффер: их видно в сниппете выдачи.
PAGES = {
 "index.html": ("Palladium Site (offline).html",
  "Внедрение AI в бизнес под ключ: аудит, автоматизация, сопровождение — Palladium",
  "Palladium — технологический департамент для вашей компании",
  "Внедрение AI в бизнес: чат-боты, голосовые агенты, автоматизация процессов, локальные нейросети. Система остаётся в вашей собственности, первые результаты за 1–3 недели. Бесплатный 30-минутный разбор.",
  "/"),
 "cases.html": ("Palladium Cases (offline).html",
  "Кейсы внедрения AI: недвижимость, видеопродакшн, закупки, контроль звонков — Palladium",
  "Кейсы — Palladium",
  "Реальные кейсы внедрения AI: ответ на заявку за минуту, рекламные ролики без съёмочной группы, подбор поставщиков за ночь, разбор каждого звонка отдела продаж. Что было, что стало, что внедрили.",
  "/cases.html"),
 "products.html": ("Palladium Products (offline).html",
  "12 продуктов внедрения AI: от аудита до AI-управляемой компании — Palladium",
  "12 продуктов — Palladium",
  "Внедрение AI по ступеням: аудит, быстрые автоматизации, AI-оснащение отделов, цифровой двойник компании. Сроки, оплата и KPI по каждому из 12 продуктов. Начать можно с любой ступени.",
  "/products.html"),
}

LINKS = [("Palladium%20Site.dc.html","index.html"),("Palladium Site.dc.html","index.html"),
         ("Palladium%20Cases.dc.html","cases.html"),("Palladium Cases.dc.html","cases.html"),
         ("Palladium%20Products.dc.html","products.html"),("Palladium Products.dc.html","products.html")]

# Правки текста до исправления в канвасе Claude Design.
# Если правка не нашлась — значит, исходник уже исправлен: сборка сообщит, строку можно удалить.
TEXT_FIXES = [
 ("cases.html", "обходится в 500 000 ₽", "обходится в 400 000 ₽",
  "цена классического продакшна: на главной 400 000, в кейсах было 500 000 — выравнено по главной"),
 ("index.html", "За две-три недели разбираем", "За одну-две недели разбираем",
  "AI Audit: текст говорил «две-три недели», чип срока — «1–2 недели»"),
 ("products.html", "За две-три недели разбираем", "За одну-две недели разбираем",
  "AI Audit: текст говорил «две-три недели», чип срока — «1–2 недели»"),
 # Новое позиционирование (правка Тимура 02.08) — ТОЛЬКО в шапке главной.
 # Подвалы, карточка превью и описание организации намеренно оставлены прежними.
 ("index.html", "AI-интегратор · продукты и услуги · 2026",
  "Независимая альтернатива Palantir из Донецка",
  "подпись под логотипом в шапке главной"),
]

# Картинки в слоты под изображения. Заливка через канвас Claude Design не доходит
# до экспорта (хранится в .image-slots.state.json, которого в выгрузке нет), поэтому
# кладём файл в images/ и подставляем его поверх слота при сборке.
# Ключ — id слота, значение — (файл относительно корня, alt, снять_duotone).
# Третий флаг убирает синюю подложку дизайн-системы: у неё mix-blend-mode: color,
# то есть от картинки остаётся только светлота, а цвета заменяются на фирменный синий.
# Для скриншотов интерфейсов это съедает читаемость — там флаг включаем.
SLOT_IMAGES = {
 "cases.html": {
   "pd-case1": ("images/case1-crm.jpg",
     "Рабочие инструменты после внедрения: сводная таблица показателей агента, "
     "карточка объекта и уведомления координатора в Telegram", True),
   "pd-case2-a": ("images/case2-a.jpg",
     "Кадр рекламного ролика: всплеск молока и малина над вафельным стаканчиком", True),
   "pd-case2-b": ("images/case2-b.jpg",
     "Кадр рекламного ролика: героиня с мороженым «Геркулес Premium» "
     "на фоне фирменной вывески", True),
 },
}

# Посадочные страницы — обычный статический HTML без рантайма канваса.
# Шаблоны в build/landings/, сборка подставляет <!--HEAD--> и <!--METRIKA-->.
# Ключ — имя файла в корне сайта, значение — (title, description, path).
# JSON-LD для них собирается ниже (LANDING_LD), FAQ обязан слово в слово
# совпадать с видимым текстом страницы — это требование поисковиков.
LANDINGS = {
 "chat-boty.html": (
   "AI-чат-бот для бизнеса: сайт, WhatsApp, Telegram — внедрение под ключ | Palladium",
   "Внедряем AI-чат-ботов, которые консультируют по вашей базе знаний, собирают заявки и передают менеджеру готовый контекст. Сайт, WhatsApp, Telegram. Система в вашей собственности, пилот за 10–14 дней.",
   "/chat-boty.html"),
 "ai-audit.html": (
   "AI-аудит бизнеса: где теряются время и деньги и что закроет AI | Palladium",
   "За 1–2 недели разбираем процессы компании: карта потерь в часах и деньгах, задачи под AI с приоритетами, план внедрения с KPI. Фиксированная цена. Результат — план действий, а не презентация.",
   "/ai-audit.html"),
}

# Ссылки на посадочные в строке навигации канвас-страниц (дорисовывает хранитель).
NAV_LANDINGS = [
 {"href": "chat-boty.html", "label": "Чат-боты"},
 {"href": "ai-audit.html", "label": "AI-аудит"},
]

# Дополнительные разделы, которых нет в экспорте канваса. Лежат отдельными
# файлами в build/extra-cases/ — правятся как обычный HTML, без лазания в сборщик.
# Вставляются скриптом-хранителем после указанного раздела; тогда же в строку
# навигации добавляются якоря. Дублируются в build/prerender/ для роботов без JS.
EXTRA_SECTIONS = {
 "cases.html": {
   "after": "c2",                       # вставить после этого раздела
   "files": ["case3.html", "case4.html"],
   "marker": "c4",                      # если уже есть — не вставлять повторно
   "nav_after": "#c2",                  # куда в строке навигации добавить якоря
   "nav": [("#c3", "Закупки"), ("#c4", "Контроль звонков")],
 },
}

# Слоты под изображения, которые не нужны вовсе: картинки туда не планируются,
# а пустой слот занимает место и рисует рамку с засечками. Убираем весь блок
# .blueprint (рамка + угловые засечки + отступ), а не только сам слот.
HIDDEN_SLOTS = {
 "index.html": ["pd-team"],   # раздел «Команда Palladium» — фото не будет
}

NAV_HINT = """
/* Подсказка прокрутки у правого края строки навигации.
   Липкий нулевой элемент в конце строки — обёртки нет, чтобы не ломать
   перенос навигации на вторую строку на мобильном. */
[data-navlinks]>i.pd-hint{
  position:sticky;right:0;flex:0 0 0px;width:0;align-self:stretch;
  overflow:visible;pointer-events:none;
}
[data-navlinks]>i.pd-hint::before{
  content:'';position:absolute;top:0;bottom:0;right:0;width:16px;
  opacity:0;transition:opacity .28s ease;
  background:linear-gradient(90deg,
    rgba(127,212,240,0) 0%,
    rgba(127,212,240,.42) 28%,
    rgba(45,95,175,.86) 64%,
    rgba(5,10,30,.97) 100%);
}
[data-navlinks][data-more="1"]>i.pd-hint::before{opacity:.4}

/* Пустые слоты под изображения приезжают из экспорта с редакторской
   заглушкой «перетащите файл» и кнопками Replace/Edit. Посетителям это видеть
   не нужно — гасим. Когда в слот попадёт картинка, она отрисуется как обычно. */
image-slot::part(empty){display:none!important}

/* Картинка, подставленная в слот при сборке. Ложится поверх пустого слота
   в его же контейнер (у того position:relative и заданная пропорция),
   поэтому кадрируется ровно по рамке. */
.pd-slotimg{
  position:absolute;inset:0;width:100%;height:100%;
  object-fit:cover;object-position:center;display:block;
}

/* Снятие синей подложки duotone для отдельных слотов. Сам ::after не убираем —
   он может нести рамку блюпринта: гасим только заливку и режим наложения. */
.blueprint.duotone.pd-nofilter::after{
  mix-blend-mode:normal!important;background:transparent!important;
}

/* Блок с ненужным слотом убираем целиком, вместе с рамкой и отступом. */
.pd-slothidden{display:none!important}
"""

# Картинку подставляем, только если файл реально лежит на диске: пока его нет,
# слот остаётся пустым, а не ломается битой ссылкой. Сборка при этом предупреждает.
def slot_images_for(page):
    out = {}
    for slot_id, (rel, alt, nofilter) in SLOT_IMAGES.get(page, {}).items():
        if (REPO / rel).exists():
            out[slot_id] = [rel, alt, bool(nofilter)]
        else:
            print(f"  ! {page}: файла {rel} нет — слот {slot_id} оставлен пустым")
    return out


# Разделы читаются с диска; если файла нет — сборка сообщает и продолжает.
def extra_for(page):
    conf = EXTRA_SECTIONS.get(page)
    if not conf:
        return None
    parts = []
    for name in conf["files"]:
        f = pathlib.Path(__file__).resolve().parent / "extra-cases" / name
        if f.exists():
            parts.append(f.read_text(encoding="utf-8").strip())
        else:
            print(f"  ! {page}: нет файла раздела {name}")
    if not parts:
        return None
    return {"after": conf["after"], "marker": conf["marker"],
            "navAfter": conf["nav_after"],
            "nav": [{"href": h, "label": l} for h, l in conf["nav"]],
            "html": "\n".join(parts)}


# ---------------------------------------------------------------- JSON-LD

ORG = {
 "@context": "https://schema.org", "@type": "Organization",
 "@id": BASE + "/#org", "name": "Palladium", "url": BASE + "/",
 "logo": BASE + "/og-image.jpg",
 "description": "AI-интегратор: проектируем, внедряем и сопровождаем AI-системы, "
                "которые остаются в собственности клиента — на его серверах и в его аккаунтах.",
 "email": "info@palladium.com.ru", "telephone": "+79490209308",
 "address": {"@type": "PostalAddress", "addressLocality": "Донецк", "addressCountry": "RU"},
 "areaServed": "RU",
 "contactPoint": {"@type": "ContactPoint", "telephone": "+79490209308",
                  "contactType": "sales", "availableLanguage": ["Russian"]},
 "sameAs": ["https://t.me/ShirinTimur"],
}

WEBSITE = {
 "@context": "https://schema.org", "@type": "WebSite",
 "@id": BASE + "/#website", "url": BASE + "/", "name": "Palladium",
 "inLanguage": "ru", "publisher": {"@id": BASE + "/#org"},
}

FAQ = [
 ("Сколько это стоит?",
  "Зависит от ступени. Аудит и Quick Wins — фиксированная цена, известная до старта. Для системных продуктов смета появляется после диагностики: она опирается на ваши конкретные процессы, а не на среднюю температуру по рынку. Первая консультация бесплатна."),
 ("У нас беспорядок в данных и нет нормальной CRM. Нам рано?",
  "Наоборот — это типичная точка старта. Модуль Data Readiness наводит порядок в CRM и документах, а аудит покажет, что можно запускать уже сейчас. Больших проектов без чистых данных мы и сами не начинаем — если рано, скажем честно."),
 ("Наши данные уйдут в облако?",
  "Не обязательно. У нас есть собственный стек локальных моделей: AI работает на ваших серверах, данные не покидают компанию. Для юристов, клиник и финансов это часто единственный приемлемый вариант — см. модуль Private AI."),
 ("Мы не технари. Команда потянет?",
  "Интерфейсы живут там, где команда уже работает: Telegram, WhatsApp, почта, CRM. Обучение и регламенты входят во внедрение. И начинаем мы с задач, которые снимают рутину с людей, — сопротивление тает быстро."),
 ("Чем вы отличаетесь от студии, которая «сделает бота»?",
  "Бот — это функция. Мы строим систему: процессы, роли, данные, контроль качества и сопровождение. Поэтому матрица устроена лестницей: каждый продукт — ступень к управляемой AI-среде компании, а не разовая поделка."),
 ("Когда будет виден результат?",
  "На ступени Quick Wins — через 1–3 недели: сэкономленные часы видно сразу. Системные продукты дают эффект волнами, и пилот показывает результат до того, как вы вкладываетесь в полное внедрение."),
 ("Что будет с системой через полгода, когда бизнес изменится?",
  "Для этого есть Managed AI: поддержка по SLA, обновление агентов, квартальный план развития. Система, которую не сопровождают, умирает за три месяца — мы проектируем так, чтобы она развивалась вместе с бизнесом."),
 ("А если мы захотим уйти от вас?",
  "Уйдёте без потерь. Код, доступы, данные и документация с самого начала находятся в вашей собственности и на вашей инфраструктуре. Документация пишется так, чтобы систему мог принять другой подрядчик. Это записано в договоре."),
 ("Почему открытые технологии, а не известные платные сервисы?",
  "Потому что открытые решения промышленного класса делают то же самое, но оставляют вам два права, которых нет у арендованного сервиса: доработать систему под свои процессы и владеть ею. За качество отвечаем мы — договором и поддержкой."),
]

FAQPAGE = {
 "@context": "https://schema.org", "@type": "FAQPage",
 "mainEntity": [{"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ],
}

PRODUCTS = [
 ("AI Audit / AI Map", "Аудит компании за 1–2 недели: где теряются время и деньги, какие задачи AI закроет уже сейчас. План действий с приоритетами."),
 ("AI Quick Wins", "3–5 самых надоевших рутинных задач закрываются автоматизацией за 1–3 недели."),
 ("AI Workflow System", "CRM, почта, календарь, документы и задачи соединяются в сквозные цепочки с ответственными и контролем."),
 ("Department AI", "Полное AI-оснащение одного отдела: ассистент у каждого сотрудника, аналитика у руководителя."),
 ("AI Sales OS / Marketing OS / Legal OS", "Готовая AI-операционная среда для функции: роли, объекты, процессы и агенты."),
 ("Agent Mesh", "Сеть специализированных агентов с общим контекстом: заявки, документы, отчётность."),
 ("Digital Twin Lite", "Компания описывается как система: объекты, роли, действия и связи между отделами."),
 ("Digital Twin Company", "Полная цифровая модель компании: процессы, правила, статусы, права доступа, источники данных."),
 ("AI Orchestrated Company", "Оркестратор управляет агентами и процессами; руководитель видит компанию на одной панели."),
 ("Industry AI OS", "Готовая AI-операционная система под отрасль: недвижимость, клиники, юрфирмы, автодилеры, сервис, e-commerce."),
 ("AI Transformation Program", "Программа полного перехода компании на AI-native модель за 6–12 месяцев."),
 ("Managed AI / AI на подписке", "Сопровождение по SLA: качество, обновление агентов, новые сценарии, квартальный план развития."),
]

CATALOG = {
 "@context": "https://schema.org", "@type": "OfferCatalog",
 "name": "12 продуктов Palladium", "url": BASE + "/products.html",
 "provider": {"@id": BASE + "/#org"},
 "itemListElement": [{"@type": "Offer",
                      "itemOffered": {"@type": "Service", "name": n, "description": d,
                                      "provider": {"@id": BASE + "/#org"}}}
                     for n, d in PRODUCTS],
}

def crumbs(name, path):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Главная", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": name, "item": BASE + path}]}

def service_ld(name, desc, path):
    return {"@context": "https://schema.org", "@type": "Service",
            "name": name, "description": desc, "url": BASE + path,
            "provider": {"@id": BASE + "/#org"}, "areaServed": "RU",
            "availableLanguage": "ru"}

def faq_ld(pairs):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in pairs]}

FAQ_CHATBOT = [
 ("Сколько стоит чат-бот?",
  "Внедрение — фикс, зависит от числа каналов и интеграций; называем цену после бесплатного разбора, до старта работ. Сопровождение — фиксированная сумма в месяц. Платы за количество диалогов нет."),
 ("Бот не будет выдумывать и позорить компанию?",
  "Ассистент отвечает только по вашей базе знаний, на вопросы вне неё — передаёт человеку. На пилоте вы читаете реальные диалоги и утверждаете тон и границы. Качество ответов — часть SLA сопровождения."),
 ("У нас нет нормальной CRM и базы знаний. Рано?",
  "Нет. Наведение порядка — часть внедрения: соберём базу из прайсов, переписок и головы вашего лучшего менеджера. Если по-честному рано — так и скажем на разборе."),
 ("Чьи это будут данные и что будет, если мы уйдём?",
  "Ваши. Код, база знаний, промпты, история диалогов — на ваших серверах и в ваших аккаунтах, это записано в договоре. Документацию пишем так, чтобы систему мог принять другой подрядчик."),
 ("Переписка клиентов уйдёт в облачную нейросеть?",
  "По умолчанию используем модели, подходящие под задачу и бюджет. Если данные чувствительные — разворачиваем локальную модель на вашем сервере: переписка не покидает компанию."),
 ("Сколько времени занимает запуск?",
  "Первый работающий канал — обычно 2–3 недели от старта, включая диагностику и пилот."),
]

FAQ_AUDIT = [
 ("Чем это отличается от «бесплатного аудита» от студий?",
  "Бесплатный аудит — это продажа: его цель показать, что вам всё нужно. Наш аудит — платный продукт с фиксированной ценой, и его результат принадлежит вам. В нём есть раздел «что не нужно делать» — бесплатные аудиты таким не заканчиваются."),
 ("У нас беспорядок в данных, CRM ведётся кое-как. Есть смысл?",
  "Да — беспорядок и есть типичная точка старта. Аудит покажет, что можно запускать уже сейчас, а где сначала нужен порядок в данных и сколько это займёт."),
 ("Нужно ли отвлекать команду?",
  "Интервью — 30–60 минут на человека, по графику, который не ломает работу. Доступы к системам обсуждаем заранее; чувствительные данные можем разбирать на вашей территории и на локальных инструментах."),
 ("Мы небольшая компания — аудит это не для корпораций?",
  "Для компании из 5–15 человек есть экспресс-формат: разбор одного отдела или одного процесса за несколько дней. На знакомстве подберём формат под размер."),
 ("Что если окажется, что AI нам не нужен?",
  "Так и напишем — с обоснованием и расчётом. Вы сэкономите на внедрении, которое не окупилось бы. Для нас это тоже результат: репутация дороже одного контракта."),
]

LANDING_LD = {
 "chat-boty.html": [
   crumbs("AI-чат-боты", "/chat-boty.html"),
   service_ld("Внедрение AI-чат-ботов",
              "AI-ассистенты для сайта, WhatsApp и Telegram: консультируют по базе знаний компании, собирают заявки, передают менеджеру контекст разговора, пишут в CRM.",
              "/chat-boty.html"),
   faq_ld(FAQ_CHATBOT)],
 "ai-audit.html": [
   crumbs("AI-аудит", "/ai-audit.html"),
   service_ld("AI-аудит бизнеса",
              "Аудит процессов компании за 1–2 недели: карта потерь в часах и деньгах, список задач под AI с приоритетами, план внедрения с KPI. Фиксированная цена.",
              "/ai-audit.html"),
   faq_ld(FAQ_AUDIT)],
}

CASES_LIST = {
 "@context": "https://schema.org", "@type": "ItemList",
 "name": "Кейсы внедрения AI — Palladium",
 "itemListElement": [
   {"@type": "ListItem", "position": i + 1, "name": n,
    "url": BASE + "/cases.html" + anchor}
   for i, (n, anchor) in enumerate([
     ("Недвижимость: заявка перестала ждать менеджера, отчёты собираются сами", "#c1"),
     ("Видеопродакшн: рекламные ролики полного цикла без съёмочной группы", "#c2"),
     ("Закупки: отдел, который за ночь обходит весь рынок", "#c3"),
     ("Контроль звонков: разобран каждый разговор, а не пара записей в неделю", "#c4"),
   ])],
}

JSONLD = {
 "index.html":    [ORG, WEBSITE, FAQPAGE],
 "cases.html":    [crumbs("Кейсы", "/cases.html"), CASES_LIST],
 "products.html": [crumbs("12 продуктов", "/products.html"), CATALOG],
}

# ---------------------------------------------------------------- шаблоны

def static_head(title, og_title, desc, path, lds):
    og_img = BASE + "/og-image.jpg"
    tags = [
     f"<title>{title}</title>",
     '<meta name="viewport" content="width=device-width, initial-scale=1">',
     f'<meta name="description" content="{desc}">',
     '<meta name="theme-color" content="#050a1e">',
     f'<link rel="canonical" href="{BASE}{path}">',
     f'<link rel="icon" href="{FAVICON}">',
     '<link rel="icon" type="image/x-icon" sizes="32x32" href="/favicon.ico">',
     '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
     f'<meta property="og:title" content="{og_title}">',
     f'<meta property="og:description" content="{desc}">',
     f'<meta property="og:url" content="{BASE}{path}">',
     '<meta property="og:type" content="website">',
     '<meta property="og:locale" content="ru_RU">',
     '<meta property="og:site_name" content="Palladium">',
     f'<meta property="og:image" content="{og_img}">',
     '<meta property="og:image:width" content="1200">',
     '<meta property="og:image:height" content="630">',
     '<meta property="og:image:alt" content="Palladium — AI-интегратор">',
     '<meta name="twitter:card" content="summary_large_image">',
     f'<meta name="twitter:image" content="{og_img}">',
    ]
    if YANDEX_VERIFICATION:
        tags.append(f'<meta name="yandex-verification" content="{YANDEX_VERIFICATION}">')
    if GOOGLE_VERIFICATION:
        tags.append(f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION}">')
    for i, ld in enumerate(lds):
        tags.append(f'<script type="application/ld+json" id="pd-ld-{i}">'
                    + json.dumps(ld, ensure_ascii=False) + "</script>")
    return "\n".join(tags)

def metrika_tag():
    # Дословно тот блок, что стоял на сайте с 31.07.2026 (перед скриптом-хранителем).
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

# Никакой JS не нужен, чтобы прочитать страницу: пререндер виден без скриптов,
# сплэш и строку «Unpacking...» прячем.
NOSCRIPT = """<noscript>
    <style>#__bundler_loading, #__bundler_thumbnail { display: none; }</style>
  </noscript>"""

GUARD = """<script>(function(){
  var C = __CFG__;
  function meta(attr,key,val){
    var el=document.head.querySelector('meta['+attr+'="'+key+'"]');
    if(!el){el=document.createElement('meta');el.setAttribute(attr,key);document.head.appendChild(el);}
    if(el.getAttribute('content')!==val)el.setAttribute('content',val);
  }
  function link(rel,href){
    var el=document.head.querySelector('link[rel="'+rel+'"]');
    if(!el){el=document.createElement('link');el.rel=rel;document.head.appendChild(el);}
    if(el.getAttribute('href')!==href)el.setAttribute('href',href);
  }
  function fixHead(){
    if(document.documentElement.lang!==C.lang)document.documentElement.lang=C.lang;
    if(document.title!==C.title)document.title=C.title;
    for(var k in C.metaName)meta('name',k,C.metaName[k]);
    for(var k in C.metaProperty)meta('property',k,C.metaProperty[k]);
    link('icon',C.favicon); link('canonical',C.canonical);
    link('apple-touch-icon','/apple-touch-icon.png');
    if(!document.getElementById('pd-style')){
      var s=document.createElement('style');s.id='pd-style';s.textContent=C.css;
      document.head.appendChild(s);
    }
    fixLd();
  }
  // Свап документа стирает статический head вместе с JSON-LD — возвращаем.
  // Google читает разметку из отрендеренного DOM, поэтому она нужна и после свапа.
  function fixLd(){
    if(!C.jsonld)return;
    for(var i=0;i<C.jsonld.length;i++){
      var id='pd-ld-'+i;
      if(!document.getElementById(id)){
        var s=document.createElement('script');
        s.type='application/ld+json';s.id=id;
        s.textContent=JSON.stringify(C.jsonld[i]);
        document.head.appendChild(s);
      }
    }
  }
  function fixSlots(){
    var slots=document.querySelectorAll('image-slot');
    for(var i=0;i<slots.length;i++){
      var r=slots[i].shadowRoot;
      if(!r||r.getElementById('pd-slotfix'))continue;
      var st=document.createElement('style');
      st.id='pd-slotfix';
      st.textContent='.empty{display:none!important}.ctl,.spill{display:none!important}';
      r.appendChild(st);
    }
    // Подстановка картинок в слоты: кладём <img> рядом со слотом, в его контейнер.
    // Внутрь самого image-slot не лезем — там shadow DOM со своей логикой кадрирования.
    for(var id in C.slotImages){
      var host=document.getElementById(id);
      if(!host)continue;
      var box=host.parentElement;
      if(!box||box.querySelector('img.pd-slotimg'))continue;
      var im=document.createElement('img');
      im.className='pd-slotimg';
      im.src=C.slotImages[id][0];
      im.alt=C.slotImages[id][1];
      im.decoding='async';
      box.appendChild(im);
      // Снятие синей подложки, если для слота так задано.
      if(C.slotImages[id][2]){
        var bp=host.closest('.duotone');
        if(bp)bp.classList.add('pd-nofilter');
      }
    }
    // Пропорция бокса — по самой картинке. Дизайн-система на мобильном ставит
    // [data-photo]{aspect-ratio:4/3 !important}, и широкие скриншоты обрезались
    // по бокам до 42%. Инлайн с !important перебивает правило таблицы стилей.
    // Ставим везде, не только на мобильном: кадрирования не должно быть нигде.
    var imgs=document.querySelectorAll('img.pd-slotimg');
    for(var n=0;n<imgs.length;n++){
      (function(im){
        function fit(){
          if(!im.naturalWidth||!im.naturalHeight)return;
          var box=im.parentElement;
          if(!box)return;
          var want=im.naturalWidth+' / '+im.naturalHeight;
          if(box.style.getPropertyValue('aspect-ratio')!==want)
            box.style.setProperty('aspect-ratio',want,'important');
        }
        if(im.complete)fit();
        if(!im.dataset.pdFit){im.dataset.pdFit='1';im.addEventListener('load',fit);}
      })(imgs[n]);
    }
    // Ненужные слоты: прячем весь блок .blueprint — иначе останется пустая
    // рамка с засечками и её отступ. Если обёртки нет, поднимаемся на два
    // уровня: слот → контейнер с пропорцией → блок.
    for(var k=0;k<(C.hiddenSlots||[]).length;k++){
      var h=document.getElementById(C.hiddenSlots[k]);
      if(!h)continue;
      var box=h.closest('.blueprint')||(h.parentElement&&h.parentElement.parentElement);
      if(box&&!box.classList.contains('pd-slothidden'))box.classList.add('pd-slothidden');
    }
  }
  // Карточка «Сайт → palladium.com.ru» в контактах ссылается сама на себя и не
  // приносит пользы — превращаем её в прямой переход в WhatsApp с готовым
  // сообщением. Рантайм может пересобрать блок — тогда флаг data-pd-wa исчезнет
  // и карточка переделается на следующем тике.
  function fixWa(){
    if(!C.wa)return;
    var sec=document.getElementById('kontakty');
    if(!sec)return;
    var links=sec.querySelectorAll('a');
    for(var i=0;i<links.length;i++)if(links[i].getAttribute('data-pd-wa'))return;
    for(var i=0;i<links.length;i++){
      var a=links[i],spans=a.querySelectorAll('span');
      if(!spans.length)continue;
      var label=spans[0].textContent.replace(/\\s+/g,' ').trim();
      if(label==='Телефон / WhatsApp'){spans[0].textContent='Телефон';continue;}
      if(spans.length>=2&&label==='Сайт'){
        a.href='https://wa.me/'+C.wa.num+'?text='+encodeURIComponent(C.wa.text);
        a.target='_blank';a.rel='noopener';
        a.setAttribute('data-pd-wa','1');
        spans[0].textContent='WhatsApp';
        spans[1].textContent='Написать в WhatsApp →';
      }
    }
  }
  // Якорная навигация сломана дважды: свап документа съедает переход по
  // /#kontakty при заходе, а клики по якорям внутри страницы обрывает сам
  // рантайм — секции раскрываются только при прокрутке через них, браузерный
  // smooth-скролл гибнет на первой же перерисовке. Поэтому скроллим сами,
  // покадрово, как листал бы человек: секции успевают смонтироваться, позиция
  // цели пересчитывается каждый кадр. Любое действие пользователя отменяет.
  var glideOn=false,glideStop=0,userTouched=false,glideEnd=Date.now()+12000;
  ['wheel','touchstart','keydown'].forEach(function(ev){
    document.addEventListener(ev,function(){userTouched=true;glideOn=false;},
      {passive:true,capture:true});
  });
  function startGlide(){
    if(glideOn||userTouched)return;
    glideOn=true;glideStop=Date.now()+7000;
    var okFrames=0,last=Date.now();
    // Не rAF: в фоновой вкладке rAF замирает и глайд повисает «в полёте».
    // Таймер с наверстыванием: видимая вкладка — шаг каждые ~16мс, фоновая —
    // редкие тики, но каждый отрабатывает накопленные шаги синхронно.
    (function step(){
      if(!glideOn||Date.now()>glideStop){glideOn=false;return;}
      var iters=Math.max(1,Math.min(40,Math.round((Date.now()-last)/16)));
      last=Date.now();
      for(var k=0;k<iters;k++){
        if(document.getElementById('pd-prerender'))break;
        if(!location.hash){glideOn=false;return;}
        var el=null;
        try{el=document.getElementById(location.hash.slice(1));}catch(e){}
        if(!el)break;
        var t=el.getBoundingClientRect().top;
        if(t>-40&&t<40){
          // На буте макет дёргается и цель на миг «рядом» — прибытие
          // засчитываем только устойчивое, несколько шагов подряд.
          if(++okFrames>=5){glideOn=false;return;}
          continue;
        }
        okFrames=0;
        var mag=Math.min(Math.abs(t)*0.28+8,innerHeight*0.6);
        window.scrollBy({top:(t>0?1:-1)*mag,behavior:'instant'});
      }
      setTimeout(step,16);
    })();
  }
  // Клик по якорю — явная просьба доскроллить: снимает прежний запрет.
  // Здесь же цели Метрики: клики по контактам — главные конверсии сайта.
  // Имена целей фиксированы, под них заводятся JS-цели в кабинете Метрики:
  // click_phone, click_whatsapp, click_telegram, click_email.
  window.addEventListener('hashchange',function(){userTouched=false;startGlide();});
  document.addEventListener('click',function(e){
    var n=e.target;
    while(n&&n.nodeType===1&&n.tagName!=='A')n=n.parentNode;
    if(!n||n.nodeType!==1)return;
    var href=n.getAttribute('href')||'';
    if(href.indexOf('#')>=0){userTouched=false;setTimeout(startGlide,80);}
    var goal=href.indexOf('tel:')===0?'click_phone'
      :href.indexOf('wa.me')>=0?'click_whatsapp'
      :href.indexOf('t.me')>=0?'click_telegram'
      :href.indexOf('mailto:')===0?'click_email':null;
    if(goal&&C.metrika&&typeof ym==='function')ym(C.metrika,'reachGoal',goal);
  },true);
  // Тики syncNav: пока пользователь не вмешался и цель далеко — перезапускаем.
  function fixHash(){
    if(userTouched||!location.hash||Date.now()>glideEnd)return;
    if(glideOn||document.getElementById('pd-prerender'))return;
    var el=null;
    try{el=document.getElementById(location.hash.slice(1));}catch(e){}
    if(!el)return;
    var t=el.getBoundingClientRect().top;
    if(t<=-150||t>=150)startGlide();
  }
  // Разделы, которых нет в экспорте канваса: вставляем после указанного и
  // добавляем якоря в строку навигации. Рантайм пересобирает страницу, поэтому
  // функция идемпотентна и вызывается на каждом тике синхронизации.
  function addExtra(){
    if(!C.extra||!C.extra.html)return;
    if(!document.getElementById(C.extra.marker)){
      var host=document.getElementById(C.extra.after);
      if(host)host.insertAdjacentHTML('afterend',C.extra.html);
    }
    var row=document.querySelector('nav [data-navlinks]');
    if(!row||!C.extra.nav)return;
    var proto=row.querySelector('a[href^="#"]');
    var prev=row.querySelector('a[href="'+C.extra.navAfter+'"]')||proto;
    for(var i=0;i<C.extra.nav.length;i++){
      var it=C.extra.nav[i];
      if(row.querySelector('a[href="'+it.href+'"]'))continue;
      var a=document.createElement('a');
      a.setAttribute('href',it.href);
      a.textContent=it.label;
      if(proto){
        var st=proto.getAttribute('style'); if(st)a.setAttribute('style',st);
        var sh=proto.getAttribute('style-hover'); if(sh)a.setAttribute('style-hover',sh);
      }
      if(prev&&prev.parentNode===row)prev.insertAdjacentElement('afterend',a);
      else row.appendChild(a);
      prev=a;
    }
  }
  // Ссылки на посадочные страницы в конце строки навигации (перед подсказкой
  // прокрутки). Рантайм пересобирает навигацию — функция идемпотентна.
  function addNavLinks(){
    if(!C.navLinks)return;
    var row=document.querySelector('nav [data-navlinks]');
    if(!row)return;
    var proto=row.querySelector('a[href]');
    for(var i=0;i<C.navLinks.length;i++){
      var it=C.navLinks[i];
      if(row.querySelector('a[href="'+it.href+'"]'))continue;
      var a=document.createElement('a');
      a.setAttribute('href',it.href);
      a.textContent=it.label;
      if(proto){
        var st=proto.getAttribute('style'); if(st)a.setAttribute('style',st);
        var sh=proto.getAttribute('style-hover'); if(sh)a.setAttribute('style-hover',sh);
      }
      var hint=row.querySelector(':scope > i.pd-hint');
      if(hint)row.insertBefore(a,hint);else row.appendChild(a);
    }
  }
  function scrollers(){
    var list=document.querySelectorAll('nav [data-navlinks]');
    if(list.length)return list;
    var navs=document.querySelectorAll('nav'),acc=[];
    for(var n=0;n<navs.length;n++){
      var els=navs[n].querySelectorAll('*');
      for(var j=0;j<els.length;j++){
        var ov=getComputedStyle(els[j]).overflowX;
        if(ov==='auto'||ov==='scroll'){els[j].setAttribute('data-navlinks','');acc.push(els[j]);break;}
      }
    }
    return acc;
  }
  // Рантайм пересобирает навигацию, поэтому ничего не держим на конкретном узле:
  // каждый раз находим строку заново, дорисовываем подсказку и пересчитываем состояние.
  function syncNav(){
    var list=scrollers(),any=false;
    for(var i=0;i<list.length;i++){
      var sc=list[i];any=true;
      var hint=sc.querySelector(':scope > i.pd-hint');
      if(!hint){
        hint=document.createElement('i');
        hint.className='pd-hint';
        var gap=getComputedStyle(sc).columnGap;
        if(gap&&gap!=='normal'&&parseFloat(gap)>0)hint.style.marginLeft='-'+gap;
        sc.appendChild(hint);
      }else if(hint!==sc.lastElementChild){
        sc.appendChild(hint);
      }
      var more=sc.scrollWidth-sc.clientWidth-sc.scrollLeft;
      var val=more>4?'1':'0';
      if(sc.getAttribute('data-more')!==val)sc.setAttribute('data-more',val);
    }
    addExtra();
    addNavLinks();
    fixSlots();
    fixLd();
    fixWa();
    fixHash();
    return any;
  }
  document.addEventListener('scroll',syncNav,true);
  window.addEventListener('resize',syncNav);
  window.addEventListener('load',syncNav);
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(syncNav);
  var navTimer=setInterval(syncNav,300);
  setTimeout(function(){clearInterval(navTimer);setInterval(syncNav,2000);},15000);
  fixHead();
  document.addEventListener('DOMContentLoaded',fixHead);
  new MutationObserver(fixHead).observe(document.head,{childList:true});
  var tries=0;
  var bodyObs=new MutationObserver(function(){
    fixHead();
    if(syncNav()||++tries>60)bodyObs.disconnect();
  });
  if(document.body)bodyObs.observe(document.body,{childList:true,subtree:true});
  else document.addEventListener('DOMContentLoaded',function(){bodyObs.observe(document.body,{childList:true,subtree:true});});
  syncNav(); setTimeout(syncNav,400); setTimeout(syncNav,1200);
})();</script>
</body>"""

# ---------------------------------------------------------------- сборка

def build():
    for name, (srcname, title, og_title, desc, path) in PAGES.items():
        html = (SRC / srcname).read_text(encoding="utf-8")
        for a, b in LINKS:
            html = html.replace(a, b)
        assert ".dc.html" not in html, name

        for f_name, old, new, why in TEXT_FIXES:
            if f_name != name:
                continue
            if old in html:
                html = html.replace(old, new)
            else:
                print(f"  ⚠ {name}: правка не нашлась (видимо, исправлено в канвасе — строку можно удалить): {why}")

        # 1. Статический head вместо заводского <title>Bundled Page</title>,
        #    и язык документа — на корневом теге, до всякого JS.
        assert html.index("<html>") < 200, name  # корневой тег, не <html> в JS-строках
        html = html.replace("<html>", '<html lang="ru">', 1)
        assert "<title>Bundled Page</title>" in html, name
        html = html.replace("<title>Bundled Page</title>",
                            static_head(title, og_title, desc, path, JSONLD[name]), 1)

        # 3. Пререндер сразу после строки «Unpacking...»
        pre = (PRERENDER_DIR / name).read_text(encoding="utf-8")
        anchor = '<div id="__bundler_loading">Unpacking...</div>'
        assert anchor in html, name
        html = html.replace(anchor, anchor + "\n" + pre, 1)

        # Прежний noscript «This page requires JavaScript» больше не прав:
        # страница читается и без JS — пререндером.
        html = re.sub(r"<noscript>.*?</noscript>", NOSCRIPT, html, count=1, flags=re.S)

        # 5. Скрипт-хранитель перед </body>
        meta_name = {"description": desc, "theme-color": "#050a1e",
                     "twitter:card": "summary_large_image",
                     "twitter:image": BASE + "/og-image.jpg"}
        if YANDEX_VERIFICATION:
            meta_name["yandex-verification"] = YANDEX_VERIFICATION
        if GOOGLE_VERIFICATION:
            meta_name["google-site-verification"] = GOOGLE_VERIFICATION
        cfg = json.dumps({
          "title": title, "lang": "ru", "favicon": FAVICON, "canonical": BASE + path,
          "css": NAV_HINT,
          "metaName":     meta_name,
          "metaProperty": {"og:title": og_title, "og:description": desc, "og:url": BASE + path,
                           "og:type": "website", "og:locale": "ru_RU", "og:site_name": "Palladium",
                           "og:image": BASE + "/og-image.jpg",
                           "og:image:width": "1200", "og:image:height": "630",
                           "og:image:alt": "Palladium — AI-интегратор"},
          "jsonld": JSONLD[name],
          "wa": {"num": WA_NUM, "text": WA_TEXT},
          "metrika": METRIKA_ID,
          "navLinks": NAV_LANDINGS,
          "slotImages": slot_images_for(name),
          "hiddenSlots": HIDDEN_SLOTS.get(name, []),
          "extra": extra_for(name),
        }, ensure_ascii=False)

        # 7. Метрика + скрипт-хранитель перед </body>
        tail = (metrika_tag() if METRIKA_ID else "") + GUARD.replace("__CFG__", cfg)
        assert "</body>" in html, name
        html = html.replace("</body>", tail, 1)
        (OUT / name).write_text(html, encoding="utf-8")
        print(f"{name:15s} → {title}")

    # Посадочные: обычный HTML, подставляем head, Метрику и цели.
    goals_js = ("""<script>document.addEventListener('click',function(e){
var n=e.target;while(n&&n.nodeType===1&&n.tagName!=='A')n=n.parentNode;
if(!n||n.nodeType!==1)return;var h=n.getAttribute('href')||'';
var g=h.indexOf('tel:')===0?'click_phone':h.indexOf('wa.me')>=0?'click_whatsapp'
:h.indexOf('t.me')>=0?'click_telegram':h.indexOf('mailto:')===0?'click_email':null;
if(g&&typeof ym==='function')ym(""" + METRIKA_ID + """,'reachGoal',g);},true);</script>""")
    landings_dir = pathlib.Path(__file__).resolve().parent / "landings"
    for name, (title, desc, path) in LANDINGS.items():
        tpl = (landings_dir / name).read_text(encoding="utf-8")
        assert "<!--HEAD-->" in tpl and "<!--METRIKA-->" in tpl, name
        tpl = tpl.replace("<!--HEAD-->", static_head(title, title, desc, path, LANDING_LD[name]), 1)
        tpl = tpl.replace("<!--METRIKA-->", (metrika_tag() if METRIKA_ID else "") + goals_js, 1)
        (OUT / name).write_text(tpl, encoding="utf-8")
        print(f"{name:15s} → {title[:60]}")

    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + BASE + "/sitemap.xml\n")

    urls = [("/", "1.0"), ("/products.html", "0.8"), ("/cases.html", "0.8"),
            ("/chat-boty.html", "0.8"), ("/ai-audit.html", "0.8")]
    items = "\n".join(
        f"  <url>\n    <loc>{BASE}{p}</loc>\n    <lastmod>{TODAY}</lastmod>\n"
        f"    <changefreq>monthly</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        for p, pr in urls)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + items + "\n</urlset>\n")

    (OUT / ".nojekyll").write_text("")
    print("\nготово:", OUT)

if __name__ == "__main__":
    build()
