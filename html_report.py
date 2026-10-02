#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime


def _esc(text):
    """Экранирует HTML."""
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #0a0a0a;
  color: #e8e8e8;
  font-family: 'Courier New', monospace;
  line-height: 1.6;
  padding: 20px;
}
.container { max-width: 900px; margin: 0 auto; }
h1, h2, h3 { color: #9b59d0; margin-bottom: 12px; }
h1 { font-size: 26px; border-bottom: 2px solid #9b59d0; padding-bottom: 10px; }
h2 { font-size: 20px; margin-top: 20px; }
.header { text-align: center; margin-bottom: 30px; }
.header .bot { color: #e74c3c; font-weight: bold; }
.section {
  background: #111;
  border: 1px solid rgba(155, 89, 208, 0.3);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.section p { margin-bottom: 6px; }
.label { color: #9b59d0; font-weight: bold; }
.value { color: #e8e8e8; }
a { color: #9b59d0; text-decoration: none; word-break: break-all; }
a:hover { color: #e74c3c; }
ul { list-style: none; padding-left: 0; }
li { padding: 6px 0; border-bottom: 1px dashed rgba(155, 89, 208, 0.2); }
li:last-child { border-bottom: none; }
.good { color: #2ecc71; }
.bad { color: #e74c3c; }
.relatives { border: 1px solid #e74c3c; }
.relatives h2 { color: #e74c3c; }
.result-item {
  padding: 10px;
  margin-bottom: 10px;
  background: #0a0a0a;
  border-left: 3px solid #9b59d0;
  border-radius: 4px;
}
.result-item .title { color: #b566e8; font-weight: bold; }
.result-item .url { color: #9b59d0; font-size: 12px; word-break: break-all; }
.result-item .snippet { color: #999; font-size: 13px; margin-top: 4px; }
.footer { text-align: center; margin-top: 30px; padding: 16px; color: #666; font-size: 12px; border-top: 1px solid rgba(155, 89, 208, 0.3); }
.footer .bot { color: #e74c3c; }
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  margin-left: 8px;
}
.badge-info { background: rgba(155, 89, 208, 0.3); color: #b566e8; }
.badge-target { background: rgba(231, 76, 60, 0.3); color: #e74c3c; }
"""


def _wrap(title, body):
    """Оборачивает body в HTML."""
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>""" + _esc(title) + """</title>
<style>""" + CSS + """</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>""" + _esc(title) + """</h1>
  <p>Сгенерировано <span class="bot">@paytinov_bot</span></p>
</div>
""" + body + """
<div class="footer">
  <p>Сгенерировано <span class="bot">@paytinov_bot</span></p>
  <p>""" + datetime.now().strftime("%d.%m.%Y %H:%M") + """</p>
</div>
</div>
</body>
</html>"""


# ============ НОМЕР ============
def generate_phone(phone, info, tg, wa, results, dorks):
    """HTML для поиска по номеру."""
    body = '<div class="section">\n<h2>📱 Номер: ' + _esc(phone) + '</h2>\n'

    if info:
        body += '<p><span class="label">✅ Валидный:</span> <span class="good">да</span></p>\n'
        body += '<p><span class="label">📡 Оператор:</span> ' + _esc(info.get("operator") or "?") + '</p>\n'
        body += '<p><span class="label">🏙 Регион:</span> ' + _esc(info.get("region") or "?") + '</p>\n'
        if info.get("type"):
            body += '<p><span class="label">📞 Тип:</span> ' + _esc(info["type"]) + '</p>\n'
        if info.get("timezone"):
            body += '<p><span class="label">🕐 TZ:</span> ' + _esc(", ".join(info["timezone"])) + '</p>\n'
    else:
        body += '<p><span class="label">❌ Валидный:</span> <span class="bad">нет</span></p>\n'

    body += "</div>\n"

    body += '<div class="section">\n<h2>🔗 Соцсети</h2>\n'
    if tg.get("found"):
        body += '<p><span class="label">✅ Telegram:</span> ' + _esc(tg.get("name", "есть")) + ' — <a href="' + _esc(tg.get("link", "")) + '">' + _esc(tg.get("link", "")) + '</a></p>\n'
    else:
        body += '<p><span class="label">❌ Telegram:</span> не найден</p>\n'
    if wa.get("found"):
        body += '<p><span class="label">✅ WhatsApp:</span> <a href="' + _esc(wa.get("link", "")) + '">' + _esc(wa.get("link", "")) + '</a></p>\n'
    else:
        body += '<p><span class="label">❌ WhatsApp:</span> не найден</p>\n'
    body += '<p><span class="label">🔗 VK:</span> <a href="https://vk.com/search?c[section]=people&c[q]=' + _esc(phone) + '">поиск людей</a></p>\n'
    body += "</div>\n"

    if results:
        body += '<div class="section">\n<h2>🔍 Найдено в интернете (' + str(len(results)) + ')</h2>\n'
        for r in results[:50]:
            body += '<div class="result-item">\n'
            body += '<div class="title">' + _esc(r.get("title", "")[:120]) + '</div>\n'
            body += '<div class="url"><a href="' + _esc(r.get("url", "")) + '">' + _esc(r.get("url", "")) + '</a></div>\n'
            if r.get("snippet"):
                body += '<div class="snippet">' + _esc(r["snippet"][:300]) + '</div>\n'
            body += '</div>\n'
        body += "</div>\n"

    if dorks:
        body += '<div class="section">\n<h2>🔍 Dorks (' + str(len(dorks)) + ')</h2>\n<ul>\n'
        for d in dorks:
            body += '<li>' + _esc(d) + '</li>\n'
        body += '</ul>\n</div>\n'

    return _wrap("Поиск по номеру: " + phone, body)


# ============ ФИО ============
def generate_fio(fio, results, dorks):
    """HTML для поиска по ФИО."""
    body = '<div class="section">\n<h2>📛 ФИО: ' + _esc(fio) + '</h2>\n'
    body += '<p><span class="label">🔍 Запросов:</span> ' + str(len(results)) + '</p>\n'
    body += "</div>\n"

    if results:
        body += '<div class="section">\n<h2>🔍 Найдено в интернете</h2>\n'
        for r in results[:50]:
            body += '<div class="result-item">\n'
            body += '<div class="title">' + _esc(r.get("title", "")[:120]) + '</div>\n'
            body += '<div class="url"><a href="' + _esc(r.get("url", "")) + '">' + _esc(r.get("url", "")) + '</a></div>\n'
            if r.get("snippet"):
                body += '<div class="snippet">' + _esc(r["snippet"][:300]) + '</div>\n'
            body += '</div>\n'
        body += "</div>\n"

    if dorks:
        body += '<div class="section">\n<h2>🔍 Dorks</h2>\n<ul>\n'
        for d in dorks:
            body += '<li>' + _esc(d) + '</li>\n'
        body += '</ul>\n</div>\n'

    return _wrap("Поиск по ФИО: " + fio, body)


# ============ EMAIL ============
def generate_email(email, results, dorks):
    """HTML для поиска по email."""
    body = '<div class="section">\n<h2>📧 Email: ' + _esc(email) + '</h2>\n'
    body += '<p><span class="label">🔍 Запросов:</span> ' + str(len(results)) + '</p>\n'
    body += "</div>\n"

    if results:
        body += '<div class="section">\n<h2>🔍 Найдено в интернете</h2>\n'
        for r in results[:50]:
            body += '<div class="result-item">\n'
            body += '<div class="title">' + _esc(r.get("title", "")[:120]) + '</div>\n'
            body += '<div class="url"><a href="' + _esc(r.get("url", "")) + '">' + _esc(r.get("url", "")) + '</a></div>\n'
            if r.get("snippet"):
                body += '<div class="snippet">' + _esc(r["snippet"][:300]) + '</div>\n'
            body += '</div>\n'
        body += "</div>\n"

    if dorks:
        body += '<div class="section">\n<h2>🔍 Dorks</h2>\n<ul>\n'
        for d in dorks:
            body += '<li>' + _esc(d) + '</li>\n'
        body += '</ul>\n</div>\n'

    return _wrap("Поиск по Email: " + email, body)


# ============ НИК ============
def generate_nick(nick, platforms_found):
    """HTML для поиска по нику."""
    body = '<div class="section">\n<h2>👤 Ник: ' + _esc(nick) + '</h2>\n'
    body += '<p><span class="label">✅ Найдено на платформах:</span> ' + str(len(platforms_found)) + '</p>\n'
    body += "</div>\n"

    if platforms_found:
        body += '<div class="section">\n<h2>🔗 Платформы</h2>\n<ul>\n'
        for p in platforms_found:
            body += '<li><span class="good">✅</span> ' + _esc(p.get("title", "")) + ' — <a href="' + _esc(p.get("url", "")) + '">' + _esc(p.get("url", "")) + '</a></li>\n'
        body += '</ul>\n</div>\n'
    else:
        body += '<div class="section">\n<p class="bad">❌ Ник нигде не найден.</p>\n</div>\n'

    return _wrap("Поиск по нику: " + nick, body)


# ============ IP ============
def generate_ip(ip, data):
    """HTML для поиска по IP."""
    body = '<div class="section">\n<h2>📡 IP: ' + _esc(ip) + '</h2>\n'
    body += '<p><span class="label">🌍 Страна:</span> ' + _esc(data.get("country") or "?") + '</p>\n'
    body += '<p><span class="label">🏙 Регион:</span> ' + _esc(data.get("region") or "?") + '</p>\n'
    body += '<p><span class="label">🏘 Город:</span> ' + _esc(data.get("city") or "?") + '</p>\n'
    body += '<p><span class="label">📍 Координаты:</span> ' + str(data.get("lat")) + ', ' + str(data.get("lon")) + '</p>\n'
    body += '<p><span class="label">🕐 TZ:</span> ' + _esc(data.get("timezone") or "?") + '</p>\n'
    body += '<p><span class="label">📶 ISP:</span> ' + _esc(data.get("isp") or "?") + '</p>\n'
    body += '<p><span class="label">🏢 Организация:</span> ' + _esc(data.get("org") or "?") + '</p>\n'
    body += '<p><span class="label">🔢 AS:</span> ' + _esc(data.get("as") or "?") + '</p>\n'
    body += "</div>\n"
    return _wrap("IP: " + ip, body)


# ============ ДОМЕН ============
def generate_domain(domain, data):
    """HTML для поиска по домену."""
    body = '<div class="section">\n<h2>🌐 Домен: ' + _esc(domain) + '</h2>\n'
    if data.get("ip"):
        body += '<p><span class="label">📡 IP:</span> ' + _esc(data["ip"]) + '</p>\n'
    if data.get("country"):
        body += '<p><span class="label">🌍 Страна:</span> ' + _esc(data["country"]) + '</p>\n'
    if data.get("city"):
        body += '<p><span class="label">🏙 Город:</span> ' + _esc(data["city"]) + '</p>\n'
    if data.get("isp"):
        body += '<p><span class="label">📶 ISP:</span> ' + _esc(data["isp"]) + '</p>\n'
    if data.get("registrar"):
        body += '<p><span class="label">📋 Регистратор:</span> ' + _esc(data["registrar"]) + '</p>\n'
    if data.get("created"):
        body += '<p><span class="label">📅 Создан:</span> ' + _esc(data["created"]) + '</p>\n'
    if data.get("expires"):
        body += '<p><span class="label">📅 Истекает:</span> ' + _esc(data["expires"]) + '</p>\n'
    body += "</div>\n"
    return _wrap("Домен: " + domain, body)


# ============ ВК ============
def generate_vk(data):
    """HTML для анализа ВК."""
    p = data.get("profile") or {}
    name = (_esc(p.get("first_name", "")) + " " + _esc(p.get("last_name", ""))).strip()
    vk_id = p.get("id", "")
    city = (p.get("city") or {}).get("title") if isinstance(p.get("city"), dict) else None
    bdate = p.get("bdate", "")
    status = p.get("status", "")
    site = p.get("site", "")
    about = p.get("about", "")
    online = p.get("online", 0)

    body = '<div class="section">\n<h2>👤 Профиль</h2>\n'
    body += '<p><span class="label">Имя:</span> ' + name + '</p>\n'
    body += '<p><span class="label">ID:</span> ' + str(vk_id) + '</p>\n'
    body += '<p><span class="label">Ссылка:</span> <a href="https://vk.com/id' + str(vk_id) + '">vk.com/id' + str(vk_id) + '</a></p>\n'
    if bdate:
        body += '<p><span class="label">🎂 ДР:</span> ' + _esc(bdate) + '</p>\n'
    if city:
        body += '<p><span class="label">🏙 Город:</span> ' + _esc(city) + '</p>\n'
    if status:
        body += '<p><span class="label">📝 Статус:</span> ' + _esc(status) + '</p>\n'
    if site:
        body += '<p><span class="label">🌐 Сайт:</span> <a href="' + _esc(site) + '">' + _esc(site) + '</a></p>\n'
    if about:
        body += '<p><span class="label">ℹ️ О себе:</span> ' + _esc(about) + '</p>\n'
    body += '<p><span class="label">🟢 Онлайн:</span> ' + ("да" if online else "нет") + '</p>\n'
    body += '</div>\n'

    relatives = data.get("relatives", [])
    if relatives:
        body += '<div class="section relatives">\n<h2>👨‍👩‍👧 Возможные родственники (' + str(len(relatives)) + ')</h2>\n<ul>\n'
        for r in relatives:
            body += '<li><a href="https://vk.com/id' + str(r["id"]) + '">' + _esc(r["name"]) + '</a>'
            if r.get("city"):
                body += ' — ' + _esc(r["city"])
            if r.get("bdate"):
                body += ' — 🎂 ' + _esc(r["bdate"])
            body += '</li>\n'
        body += '</ul>\n</div>\n'

    friends = data.get("friends", [])
    friends_total = data.get("friends_total", len(friends))
    body += '<div class="section">\n<h2>👥 Друзья (всего: ' + str(friends_total) + ')</h2>\n'
    if friends:
        body += '<ul>\n'
        for f in friends[:100]:
            fname = _esc(f.get("first_name", "")) + " " + _esc(f.get("last_name", ""))
            body += '<li><a href="https://vk.com/id' + str(f["id"]) + '">' + fname + '</a></li>\n'
        if len(friends) > 100:
            body += '<li>... и ещё ' + str(len(friends) - 100) + '</li>\n'
        body += '</ul>\n'
    else:
        body += '<p>Друзья скрыты или недоступны.</p>\n'
    body += '</div>\n'

    groups = data.get("groups", [])
    if groups:
        body += '<div class="section">\n<h2>🌐 Группы (' + str(len(groups)) + ')</h2>\n<ul>\n'
        for g in groups[:50]:
            body += '<li><a href="https://vk.com/club' + str(g.get("id")) + '">' + _esc(g.get("name", "")) + '</a></li>\n'
        body += '</ul>\n</div>\n'

    body += '<div class="section">\n<h2>📊 Активность</h2>\n'
    body += '<p><span class="label">📸 Фото:</span> ' + str(data.get("photos_count", 0)) + '</p>\n'
    body += '<p><span class="label">📝 Записей:</span> ' + str(data.get("wall_count", 0)) + '</p>\n</div>\n'

    return _wrap("Анализ ВК: " + name, body)
