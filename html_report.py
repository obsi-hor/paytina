#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime


def _esc(text):
    """Экранирует HTML."""
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_html(data, title="Анализ ВК"):
    """Генерирует HTML-отчёт."""
    p = data.get("profile") or {}
    name = (_esc(p.get("first_name", "")) + " " + _esc(p.get("last_name", ""))).strip()
    vk_id = p.get("id", "")
    city = (p.get("city") or {}).get("title") if isinstance(p.get("city"), dict) else None
    bdate = p.get("bdate", "")
    status = p.get("status", "")
    site = p.get("site", "")
    about = p.get("about", "")
    online = p.get("online", 0)
    last_seen = p.get("last_seen", {}).get("time") if isinstance(p.get("last_seen"), dict) else None

    # Друзья
    friends = data.get("friends", [])
    friends_total = data.get("friends_total", len(friends))

    # Родственники
    relatives = data.get("relatives", [])

    # Группы
    groups = data.get("groups", [])

    html = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>""" + _esc(title) + """</title>
<style>
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
h1 { font-size: 28px; border-bottom: 2px solid #9b59d0; padding-bottom: 10px; }
h2 { font-size: 20px; margin-top: 24px; }
h3 { font-size: 16px; color: #b566e8; }
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
.section .label { color: #9b59d0; }
a { color: #9b59d0; text-decoration: none; }
a:hover { color: #e74c3c; }
ul { list-style: none; padding-left: 0; }
li { padding: 6px 0; border-bottom: 1px dashed rgba(155, 89, 208, 0.2); }
li:last-child { border-bottom: none; }
.relatives { border: 1px solid #e74c3c; }
.relatives h2 { color: #e74c3c; }
.footer { text-align: center; margin-top: 30px; padding: 16px; color: #666; font-size: 12px; border-top: 1px solid rgba(155, 89, 208, 0.3); }
.footer .bot { color: #e74c3c; }
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>""" + _esc(title) + """</h1>
  <p>Сгенерировано <span class="bot">@paytinov_bot</span></p>
</div>

<div class="section">
  <h2>👤 Профиль</h2>
  <p><span class="label">Имя:</span> """ + name + """</p>
  <p><span class="label">ID:</span> """ + str(vk_id) + """</p>
  <p><span class="label">Ссылка:</span> <a href="https://vk.com/id""" + str(vk_id) + """">vk.com/id""" + str(vk_id) + """</a></p>
"""
    if bdate:
        html += '<p><span class="label">ДР:</span> ' + _esc(bdate) + '</p>\n'
    if city:
        html += '<p><span class="label">Город:</span> ' + _esc(city) + '</p>\n'
    if status:
        html += '<p><span class="label">Статус:</span> ' + _esc(status) + '</p>\n'
    if site:
        html += '<p><span class="label">Сайт:</span> <a href="' + _esc(site) + '">' + _esc(site) + '</a></p>\n'
    if about:
        html += '<p><span class="label">О себе:</span> ' + _esc(about) + '</p>\n'
    html += '<p><span class="label">Онлайн:</span> ' + ("✅ сейчас" if online else "❌ не в сети") + '</p>\n'
    html += '</div>\n'

    # Родственники
    if relatives:
        html += '<div class="section relatives">\n'
        html += '<h2>👨‍👩‍👧 Возможные родственники (' + str(len(relatives)) + ')</h2>\n'
        html += '<ul>\n'
        for r in relatives:
            html += '<li><a href="https://vk.com/id' + str(r["id"]) + '">' + _esc(r["name"]) + '</a>'
            if r.get("city"):
                html += ' — ' + _esc(r["city"])
            if r.get("bdate"):
                html += ' — ' + _esc(r["bdate"])
            html += '</li>\n'
        html += '</ul>\n</div>\n'

    # Друзья
    html += '<div class="section">\n'
    html += '<h2>👥 Друзья (всего: ' + str(friends_total) + ')</h2>\n'
    if friends:
        html += '<ul>\n'
        for f in friends[:100]:
            fname = _esc(f.get("first_name", "")) + " " + _esc(f.get("last_name", ""))
            html += '<li><a href="https://vk.com/id' + str(f["id"]) + '">' + fname + '</a></li>\n'
        if len(friends) > 100:
            html += '<li>... и ещё ' + str(len(friends) - 100) + '</li>\n'
        html += '</ul>\n'
    else:
        html += '<p>Друзья скрыты или недоступны.</p>\n'
    html += '</div>\n'

    # Группы
    if groups:
        html += '<div class="section">\n'
        html += '<h2>🌐 Группы (' + str(len(groups)) + ')</h2>\n'
        html += '<ul>\n'
        for g in groups[:50]:
            gname = _esc(g.get("name", ""))
            gid = g.get("id")
            html += '<li><a href="https://vk.com/club' + str(gid) + '">' + gname + '</a></li>\n'
        html += '</ul>\n</div>\n'

    # Фото и стена
    html += '<div class="section">\n'
    html += '<h2>📊 Активность</h2>\n'
    html += '<p><span class="label">Фото:</span> ' + str(data.get("photos_count", 0)) + '</p>\n'
    html += '<p><span class="label">Записей на стене:</span> ' + str(data.get("wall_count", 0)) + '</p>\n'
    html += '</div>\n'

    # Подвал
    html += '<div class="footer">\n'
    html += '<p>Сгенерировано <span class="bot">@paytinov_bot</span></p>\n'
    html += '<p>' + datetime.now().strftime("%d.%m.%Y %H:%M") + '</p>\n'
    html += '</div>\n'

    html += '</div>\n</body>\n</html>'
    return html
