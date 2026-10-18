# Palladium — сайт

Внешний AI-отдел. Статический сайт на GitHub Pages, домен palladium.com.ru (HTTPS).

## Страницы

| Файл | Страница |
|---|---|
| `index.html` | Главная |
| `videoanalitika.html` | Palladium Vision — видеоаналитика |
| `sotrudniki.html` | Цифровые сотрудники |
| `uslugi.html` | Услуги: 4 направления |
| `cases.html` | Кейсы |
| `o-kompanii.html` | О компании |
| `chat-boty.html`, `ai-audit.html` | Посадочные страницы |
| `products.html` | Старый адрес, переадресация на `uslugi.html` |

## Как устроено

Чистый HTML и один файл стилей `assets/site.css`, без React и сторонних скриптов,
кроме Яндекс.Метрики (счётчик 111244444). Шрифты Unbounded и Inter лежат в `assets/fonts`.

Исходники — в `build/`:

- `build/src/pages/*.html` — содержимое страниц. Первая строка — JSON с заголовком,
  описанием и хлебными крошками, дальше — содержимое `<main>`;
- `build/src/assets/` — стили, шрифты, картинки;
- `build/build.py` — добавляет шапку, подвал, контакты, `<head>`, разметку для поисковиков
  (FAQ собирается из видимых вопросов на странице), Метрику, `robots.txt` и `sitemap.xml`,
  проверяет битые ссылки.

`.nojekyll` обязателен: без него GitHub Pages прогоняет сборку через Jekyll.

## Обновление сайта

```
python3 build/build.py --preview   # build/preview — посмотреть локально, без Метрики
python3 build/build.py             # build/dist — версия для сайта
cp -R build/dist/. ./              # обновить файлы в корне
git add -A && git commit -m "…" && git push
python3 build/indexnow.py          # сообщить Яндексу и Bing об изменениях
```

Если страницу удалили из исходников, её файл в корне нужно удалить вручную.
