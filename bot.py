#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import re
import time
import socket
import requests
import telebot
from telebot import types
from flask import Flask, request
from threading import Thread
from datetime import date

import ddg
import phone as ph
import vk_api as vk
import vk_analysis as va
import html_report as hr

# ============ НАСТРОЙКИ ============
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DAILY_LIMIT = 30
MIRROR_BONUS = 1
START_IMAGE = "https://i.imgur.com/zuH2Cp3.jpeg"

print("[DEBUG] Токен: " + str(len(BOT_TOKEN)))
print("[DEBUG] VK: " + str(len(vk.VK_TOKEN)))

# ============ ЛИМИТЫ ============
user_limits = {}


def get_limits(user_id):
    today = date.today()
    if user_id not in user_limits:
        user_limits[user_id] = {"date": today, "used": 0}
    if user_limits[user_id]["date"] != today:
        user_limits[user_id] = {"date": today, "used": 0}
    return user_limits[user_id]


def requests_left(user_id):
    return max(0, DAILY_LIMIT - get_limits(user_id)["used"])


def use_request(user_id):
    if requests_left(user_id) <= 0:
        return False
    get_limits(user_id)["used"] += 1
    return True


def add_bonus(user_id, amount=MIRROR_BONUS):
    get_limits(user_id)["used"] = max(0, get_limits(user_id)["used"] - amount)


# ============ FLASK ============
app = Flask(__name__)


@app.route("/")
def home():
    return "Paytinov Bot works"


@app.route("/health")
def health():
    return "OK"


def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# ============ БОТ ============
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
bot._last_result = {}


# ============ МЕНЮ ============
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🕵️ Поиск", callback_data="menu_search"),
        types.InlineKeyboardButton("👥 Анализ ВК", callback_data="menu_vk"),
    )
    markup.add(
        types.InlineKeyboardButton("📡 IP", callback_data="menu_ip"),
        types.InlineKeyboardButton("🌐 Домен", callback_data="menu_domain"),
    )
    markup.add(
        types.InlineKeyboardButton("🔁 Зеркало", callback_data="menu_mirror"),
        types.InlineKeyboardButton("💳 Донат", callback_data="menu_donate"),
    )
    markup.add(
        types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="menu_help"),
    )
    return markup


def search_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📱 Номер", callback_data="search_phone"),
        types.InlineKeyboardButton("📛 ФИО", callback_data="search_fio"),
    )
    markup.add(
        types.InlineKeyboardButton("📧 Email", callback_data="search_email"),
        types.InlineKeyboardButton("👤 Ник", callback_data="search_nick"),
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="menu_back"))
    return markup


def back_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💾 Скачать HTML", callback_data="export_html"),
        types.InlineKeyboardButton("🔄 Новый поиск", callback_data="menu_search"),
    )
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="menu_back"))
    return markup


def send_main_menu(chat_id):
    try:
        bot.send_message(chat_id, "🔮 Меню:", reply_markup=main_menu())
    except Exception as e:
        print("[ERROR] send_main_menu: " + str(e))
      # ============ ОБРАБОТЧИКИ ============
if bot:
    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        caption = (
            "> INITIALIZING PAUTINA...\n"
            "> OSINT SYSTEM ONLINE\n"
            "> CONNECTION SECURED\n\n"
            "┌────────────────────────────┐\n"
            "│   🕸️  P A U T I N A       │\n"
            "│   Open Source Intelligence │\n"
            "└────────────────────────────┘\n\n"
            "[ SYSTEM INFO ]\n"
            "├─ Лимит: " + str(DAILY_LIMIT) + " / сутки\n"
            "├─ Зеркало: +" + str(MIRROR_BONUS) + " запрос\n"
            "└─ Донат: поддержать автора\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "[ ВЫБЕРИ ДЕЙСТВИЕ ]"
        )
        try:
            bot.send_photo(message.chat.id, START_IMAGE, caption=caption, reply_markup=main_menu())
        except Exception:
            bot.send_message(message.chat.id, caption, reply_markup=main_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "menu_back")
    def cb_back(call):
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text("🔮 Главное меню:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        except Exception:
            send_main_menu(call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "menu_search")
    def cb_search(call):
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text("🕵️ Тип поиска:", call.message.chat.id, call.message.message_id, reply_markup=search_menu())
        except Exception:
            bot.send_message(call.message.chat.id, "🕵️ Тип поиска:", reply_markup=search_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "menu_help")
    def cb_help(call):
        bot.answer_callback_query(call.id)
        text = (
            "ℹ️ ПОМОЩЬ\n\n"
            "🕵️ Поиск — номер, ФИО, email, ник.\n"
            "👥 Анализ ВК — профиль, друзья, родственники.\n"
            "📡 IP — гео, ISP.\n"
            "🌐 Домен — регистратор, IP.\n"
            "🔁 Зеркало — +1 запрос.\n"
            "💳 Донат — поддержать автора.\n\n"
            "📊 Лимит: " + str(DAILY_LIMIT) + " запросов/сутки."
        )
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=main_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "menu_profile")
    def cb_profile(call):
        bot.answer_callback_query(call.id)
        uid = call.from_user.id
        left = requests_left(uid)
        text = (
            "👤 ПРОФИЛЬ\n"
            "━━━━━━━━━━━━━━━\n"
            "🆔 ID: " + str(uid) + "\n"
            "📊 Осталось: " + str(left) + "/" + str(DAILY_LIMIT) + "\n"
        )
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=main_menu())

    # ============ IP ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_ip")
    def cb_ip(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📡 Введи IP:")
        bot.register_next_step_handler(msg, process_ip)

    def process_ip(message):
        uid = message.from_user.id
        ip = message.text.strip()
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            bot.send_message(message.chat.id, "❌ Неверный IP")
            send_main_menu(message.chat.id)
            return
        if not use_request(uid):
            bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
            send_main_menu(message.chat.id)
            return
        bot.send_message(message.chat.id, "🔍 Ищу...")
        try:
            r = requests.get(
                "http://ip-api.com/json/" + ip,
                params={"fields": "status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as"},
                timeout=10,
            )
            d = r.json()
            if d.get("status") != "success":
                bot.send_message(message.chat.id, "❌ Ошибка: " + str(d.get("message")))
                send_main_menu(message.chat.id)
                return
            text = "📡 IP: " + ip + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
            text += "🌍 Страна: " + str(d.get("country")) + "\n"
            text += "🏙 Регион: " + str(d.get("regionName")) + "\n"
            text += "🏘 Город: " + str(d.get("city")) + "\n"
            text += "📍 Координаты: " + str(d.get("lat")) + ", " + str(d.get("lon")) + "\n"
            text += "🕐 TZ: " + str(d.get("timezone")) + "\n"
            text += "📶 ISP: " + str(d.get("isp")) + "\n"
            text += "🔢 AS: " + str(d.get("as")) + "\n"

            bot._last_result[uid] = {
                "type": "ip",
                "ip": ip,
                "data": d,
            }
            bot.send_message(message.chat.id, text)
            bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Ошибка: " + str(e)[:200])
            send_main_menu(message.chat.id)

    # ============ ДОМЕН ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_domain")
    def cb_domain(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🌐 Введи домен:")
        bot.register_next_step_handler(msg, process_domain)

    def process_domain(message):
        uid = message.from_user.id
        domain = message.text.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
        if not re.match(r"^[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$", domain):
            bot.send_message(message.chat.id, "❌ Неверный домен")
            send_main_menu(message.chat.id)
            return
        if not use_request(uid):
            bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
            send_main_menu(message.chat.id)
            return
        bot.send_message(message.chat.id, "🔍 Ищу...")
        try:
            text = "🌐 ДОМЕН: " + domain + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
            data = {"ip": None, "country": None, "city": None, "isp": None,
                    "registrar": None, "created": None, "expires": None}

            try:
                ip = socket.gethostbyname(domain)
                data["ip"] = ip
                text += "📡 IP: " + ip + "\n"
                r = requests.get("http://ip-api.com/json/" + ip, timeout=10)
                d = r.json()
                if d.get("status") == "success":
                    data["country"] = d.get("country")
                    data["city"] = d.get("city")
                    data["isp"] = d.get("isp")
                    text += "🌍 Страна: " + str(d.get("country")) + "\n"
                    text += "🏙 Город: " + str(d.get("city")) + "\n"
                    text += "📶 ISP: " + str(d.get("isp")) + "\n"
            except Exception:
                text += "📡 IP: не определён\n"

            try:
                rq = requests.get("https://rdap.org/domain/" + domain, timeout=15)
                if rq.status_code == 200:
                    rd = rq.json()
                    for ev in rd.get("events", []):
                        if ev.get("eventAction") == "registration":
                            data["created"] = ev.get("eventDate", "")[:10]
                            text += "📅 Создан: " + data["created"] + "\n"
                        elif ev.get("eventAction") == "expiration":
                            data["expires"] = ev.get("eventDate", "")[:10]
                            text += "📅 Истекает: " + data["expires"] + "\n"
                    for ent in rd.get("entities", []):
                        if "registrar" in ent.get("roles", []):
                            vcard = ent.get("vcardArray", [])
                            if len(vcard) > 1:
                                for item in vcard[1]:
                                    if item[0] == "fn":
                                        data["registrar"] = item[3]
                                        text += "📋 Регистратор: " + item[3] + "\n"
            except Exception:
                pass

            bot._last_result[uid] = {
                "type": "domain",
                "domain": domain,
                "data": data,
            }
            bot.send_message(message.chat.id, text)
            bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Ошибка: " + str(e)[:200])
            send_main_menu(message.chat.id)
          # ============ ПОИСК: НОМЕР ============
@bot.callback_query_handler(func=lambda call: call.data == "search_phone")
def cb_search_phone(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📱 Введи номер (например +79001234567):")
    bot.register_next_step_handler(msg, process_search_phone)

def process_search_phone(message):
    uid = message.from_user.id
    phone = message.text.strip()
    if not use_request(uid):
        bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
        send_main_menu(message.chat.id)
        return
    bot.send_message(message.chat.id, "🔍 Ищу по всему миру...")

    info = ph.check_validity(phone)
    tg = ph.check_telegram(phone)
    wa = ph.check_whatsapp(phone)
    results = ddg.multi_search(ph.build_queries(phone), max_per=2)
    dorks = ph.build_dorks(phone)

    text = "📱 НОМЕР: " + phone + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if info:
        text += "✅ ВАЛИДНЫЙ\n"
        text += "📡 Оператор: " + str(info.get("operator") or "?") + "\n"
        text += "🏙 Регион: " + str(info.get("region") or "?") + "\n"
        text += "🕐 TZ: " + ", ".join(info.get("timezone", [])) + "\n\n"
    else:
        text += "❌ Номер невалидный\n\n"

    text += "🔗 Telegram: " + ("✅ " + tg.get("name", "есть") if tg.get("found") else "❌ нет") + "\n"
    text += "🔗 WhatsApp: " + ("✅ есть" if wa.get("found") else "❌ нет") + "\n"
    text += "🔗 VK: https://vk.com/search?c[section]=people&c[q]=" + phone + "\n\n"

    if results:
        text += "🔍 НАЙДЕНО (" + str(len(results)) + "):\n"
        text += ddg.format_results(results, limit=10)
    else:
        text += "❌ В интернете ничего не найдено\n"

    text += "\n🔍 DORKS (" + str(len(dorks)) + "):\n"
    for d in dorks[:10]:
        text += "  • " + d + "\n"

    bot._last_result[uid] = {
        "type": "phone",
        "phone": phone,
        "info": info,
        "tg": tg,
        "wa": wa,
        "results": results,
        "dorks": dorks,
    }

    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[i:i + 4000])
    else:
        bot.send_message(message.chat.id, text)

    bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())

# ============ ПОИСК: ФИО ============
@bot.callback_query_handler(func=lambda call: call.data == "search_fio")
def cb_search_fio(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📛 Введи ФИО (например Иванов Иван Петрович):")
    bot.register_next_step_handler(msg, process_search_fio)

def process_search_fio(message):
    uid = message.from_user.id
    fio = message.text.strip()
    if not use_request(uid):
        bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
        send_main_menu(message.chat.id)
        return
    bot.send_message(message.chat.id, "🔍 Ищу по всему миру...")

    queries = [
        '"' + fio + '"',
        'site:vk.com "' + fio + '"',
        'site:ok.ru "' + fio + '"',
        'site:instagram.com "' + fio + '"',
        'site:linkedin.com "' + fio + '"',
        'site:facebook.com "' + fio + '"',
        '"' + fio + '" резюме',
        '"' + fio + '" работа',
        '"' + fio + '" суд',
        '"' + fio + '" биография',
    ]
    results = ddg.multi_search(queries, max_per=2)
    dorks = [
        'site:vk.com "' + fio + '"',
        'site:ok.ru "' + fio + '"',
        '"' + fio + '" резюме',
        '"' + fio + '" работа',
        '"' + fio + '" суд',
    ]

    text = "📛 ФИО: " + fio + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if results:
        text += "🔍 НАЙДЕНО (" + str(len(results)) + "):\n"
        text += ddg.format_results(results, limit=15)
    else:
        text += "❌ В интернете ничего не найдено\n"

    text += "\n🔍 DORKS:\n"
    for d in dorks:
        text += "  • " + d + "\n"

    bot._last_result[uid] = {
        "type": "fio",
        "fio": fio,
        "results": results,
        "dorks": dorks,
    }

    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[i:i + 4000])
    else:
        bot.send_message(message.chat.id, text)

    bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())

# ============ ПОИСК: EMAIL ============
@bot.callback_query_handler(func=lambda call: call.data == "search_email")
def cb_search_email(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📧 Введи email:")
    bot.register_next_step_handler(msg, process_search_email)

def process_search_email(message):
    uid = message.from_user.id
    email = message.text.strip()
    if not use_request(uid):
        bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
        send_main_menu(message.chat.id)
        return
    bot.send_message(message.chat.id, "🔍 Ищу по всему миру...")

    queries = [
        '"' + email + '"',
        'site:pastebin.com "' + email + '"',
        'site:github.com "' + email + '"',
        'site:linkedin.com "' + email + '"',
        '"' + email + '" утечка',
        '"' + email + '" пароль',
    ]
    results = ddg.multi_search(queries, max_per=3)
    dorks = [
        'site:pastebin.com "' + email + '"',
        'site:github.com "' + email + '"',
        '"' + email + '" утечка',
        '"' + email + '" пароль',
    ]

    text = "📧 EMAIL: " + email + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if results:
        text += "🔍 НАЙДЕНО (" + str(len(results)) + "):\n"
        text += ddg.format_results(results, limit=15)
    else:
        text += "❌ В интернете ничего не найдено\n"

    text += "\n🔍 DORKS:\n"
    for d in dorks:
        text += "  • " + d + "\n"

    bot._last_result[uid] = {
        "type": "email",
        "email": email,
        "results": results,
        "dorks": dorks,
    }

    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[i:i + 4000])
    else:
        bot.send_message(message.chat.id, text)

    bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())

# ============ ПОИСК: НИК ============
@bot.callback_query_handler(func=lambda call: call.data == "search_nick")
def cb_search_nick(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "👤 Введи ник (без @):")
    bot.register_next_step_handler(msg, process_search_nick)

def process_search_nick(message):
    uid = message.from_user.id
    nick = message.text.strip().lstrip("@")
    if not use_request(uid):
        bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
        send_main_menu(message.chat.id)
        return
    bot.send_message(message.chat.id, "🔍 Проверяю платформы...")

    platforms = {
        "VK": "https://vk.com/" + nick,
        "Telegram": "https://t.me/" + nick,
        "Instagram": "https://instagram.com/" + nick,
        "TikTok": "https://tiktok.com/@" + nick,
        "GitHub": "https://github.com/" + nick,
        "Twitter": "https://twitter.com/" + nick,
        "YouTube": "https://youtube.com/@" + nick,
        "Reddit": "https://reddit.com/user/" + nick,
        "Twitch": "https://twitch.tv/" + nick,
        "Pinterest": "https://pinterest.com/" + nick,
        "LinkedIn": "https://linkedin.com/in/" + nick,
        "Medium": "https://medium.com/@" + nick,
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    text = "👤 НИК: " + nick + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    found = []

    for name, url in platforms.items():
        try:
            r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                text += "✅ " + name + ": " + url + "\n"
                found.append({"title": name, "url": url})
            else:
                text += "❌ " + name + "\n"
        except Exception:
            text += "❌ " + name + "\n"

    bot._last_result[uid] = {
        "type": "nick",
        "nick": nick,
        "found": found,
    }

    bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())
      # ============ АНАЛИЗ ВК ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_vk")
    def cb_vk(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "👥 Введи ссылку или ID ВК:")
        bot.register_next_step_handler(msg, process_vk)

    def process_vk(message):
        uid = message.from_user.id
        if not use_request(uid):
            bot.send_message(message.chat.id, "❌ Лимит исчерпан.")
            send_main_menu(message.chat.id)
            return
        bot.send_message(message.chat.id, "🔍 Анализирую профиль...")
        try:
            data = va.analyze_vk(message.text.strip())
            if not data:
                bot.send_message(message.chat.id, "❌ Профиль не найден или закрыт")
                send_main_menu(message.chat.id)
                return
            bot._last_result[uid] = {
                "type": "vk",
                "data": data,
            }
            html = hr.generate_vk(data)
            buf = io.BytesIO(html.encode("utf-8"))
            p = data["profile"]
            fname = p.get("first_name", "") + " " + p.get("last_name", "")
            buf.name = "vk_" + str(p.get("id", "user")) + ".html"
            bot.send_document(message.chat.id, buf, caption="📊 Анализ ВК: " + fname)
            bot.send_message(message.chat.id, "━━━━━━━━━━━━━━━\n🔽 Действия:", reply_markup=back_menu())
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Ошибка: " + str(e)[:200])
            send_main_menu(message.chat.id)

    # ============ ЗЕРКАЛО ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_mirror")
    def cb_mirror(call):
        bot.answer_callback_query(call.id)
        text = (
            "🔁 СОЗДАНИЕ ЗЕРКАЛА\n\n"
            "За каждое зеркало — +" + str(MIRROR_BONUS) + " запрос.\n"
            "Можно создавать бесконечно.\n\n"
            "1. Открой @BotFather\n"
            "2. /newbot\n"
            "3. Создай бота\n"
            "4. Скопируй токен\n"
            "5. Отправь сюда"
        )
        msg = bot.send_message(call.message.chat.id, text)
        bot.register_next_step_handler(msg, process_mirror)

    def process_mirror(message):
        uid = message.from_user.id
        token = message.text.strip()
        if not re.match(r"^\d{8,12}:[A-Za-z0-9_\-]{30,}$", token):
            bot.send_message(message.chat.id, "❌ Неверный формат токена")
            send_main_menu(message.chat.id)
            return
        try:
            r = requests.get("https://api.telegram.org/bot" + token + "/getMe", timeout=10)
            if r.status_code != 200 or not r.json().get("ok"):
                bot.send_message(message.chat.id, "❌ Токен недействителен")
                send_main_menu(message.chat.id)
                return
        except Exception:
            bot.send_message(message.chat.id, "❌ Не удалось проверить токен")
            send_main_menu(message.chat.id)
            return

        add_bonus(uid, MIRROR_BONUS)
        bot.send_message(message.chat.id, "✅ Зеркало принято! +" + str(MIRROR_BONUS) + " запрос.")
        if ADMIN_ID:
            try:
                bot.send_message(
                    ADMIN_ID,
                    "🔁 НОВОЕ ЗЕРКАЛО\nОт: " + str(uid) +
                    "\n@" + (message.from_user.username or "нет") +
                    "\nТокен: " + token
                )
            except Exception:
                pass
        send_main_menu(message.chat.id)

    # ============ ДОНАТ ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_donate")
    def cb_donate(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "💳 Введи количество звёзд (от 1 до 10000):")
        bot.register_next_step_handler(msg, process_donate)

    def process_donate(message):
        try:
            amount = int(message.text.strip())
            if amount < 1 or amount > 10000:
                raise ValueError
        except Exception:
            bot.send_message(message.chat.id, "❌ Введи число от 1 до 10000")
            send_main_menu(message.chat.id)
            return
        prices = [types.LabeledPrice(label="Поддержка автора", amount=amount)]
        try:
            bot.send_invoice(
                chat_id=message.chat.id,
                title="Поддержать автора",
                description="Спасибо за поддержку!",
                invoice_payload="donate",
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="donate",
            )
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Ошибка: " + str(e)[:150])
        send_main_menu(message.chat.id)

    @bot.pre_checkout_query_handler(func=lambda q: True)
    def pre_checkout(query):
        bot.answer_pre_checkout_query(query.id, ok=True)

    @bot.message_handler(content_types=["successful_payment"])
    def payment(message):
        amount = message.successful_payment.total_amount
        uid = message.from_user.id
        bot.send_message(message.chat.id, "💳 Спасибо за поддержку! " + str(amount) + " звёзд.")
        if ADMIN_ID:
            try:
                bot.send_message(
                    ADMIN_ID,
                    "💳 ДОНАТ\nОт: " + str(uid) +
                    "\n@" + (message.from_user.username or "нет") +
                    "\nСумма: " + str(amount) + " звёзд"
                )
            except Exception:
                pass

    # ============ HTML-ЭКСПОРТ ============
    @bot.callback_query_handler(func=lambda call: call.data == "export_html")
    def cb_export_html(call):
        bot.answer_callback_query(call.id)
        uid = call.from_user.id
        data = bot._last_result.get(uid)
        if not data:
            bot.send_message(call.message.chat.id, "❌ Результат не найден. Сначала сделай поиск.")
            return
        try:
            t = data["type"]
            if t == "phone":
                html = hr.generate_phone(data["phone"], data.get("info"), data.get("tg"), data.get("wa"), data.get("results"), data.get("dorks"))
            elif t == "fio":
                html = hr.generate_fio(data["fio"], data.get("results"), data.get("dorks"))
            elif t == "email":
                html = hr.generate_email(data["email"], data.get("results"), data.get("dorks"))
            elif t == "nick":
                html = hr.generate_nick(data["nick"], data.get("found"))
            elif t == "ip":
                html = hr.generate_ip(data["ip"], data.get("data"))
            elif t == "domain":
                html = hr.generate_domain(data["domain"], data.get("data"))
            elif t == "vk":
                html = hr.generate_vk(data["data"])
            else:
                bot.send_message(call.message.chat.id, "❌ Неизвестный тип")
                return
            buf = io.BytesIO(html.encode("utf-8"))
            buf.name = "paytinov_report.html"
            bot.send_document(call.message.chat.id, buf, caption="📄 HTML-отчёт от @paytinov_bot")
        except Exception as e:
            bot.send_message(call.message.chat.id, "❌ Ошибка: " + str(e)[:150])


# ============ WEBHOOK ============
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
    except Exception as e:
        print("[ERROR] webhook: " + str(e))
    return "OK", 200


def set_webhook():
    url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not url:
        print("[!] RENDER_EXTERNAL_URL не задан")
        return
    try:
        r = requests.post(
            "https://api.telegram.org/bot" + BOT_TOKEN + "/setWebhook",
            json={"url": url + "/webhook", "allowed_updates": ["message", "callback_query", "pre_checkout_query"]},
        )
        print("[+] Webhook: " + str(r.json()))
    except Exception as e:
        print("[ERROR] set_webhook: " + str(e))


# ============ MAIN ============
if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    if bot:
        time.sleep(3)
        set_webhook()
        print("[+] Бот запущен")
        while True:
            time.sleep(60)
