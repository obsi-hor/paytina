#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import re
import time
import requests
import telebot
from telebot import types
from flask import Flask, request
from threading import Thread
from datetime import datetime, date

import vk_api as vk
import vk_analysis as va
import html_report as hr

# ============ НАСТРОЙКИ ============
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DAILY_LIMIT = 30
MIRROR_BONUS = 1

print("[DEBUG] Токен: " + str(len(BOT_TOKEN)))
print("[DEBUG] VK: " + str(len(vk.VK_TOKEN)))

# ============ ЛИМИТЫ (в памяти) ============
user_limits = {}
mirror_tokens = []


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
        types.InlineKeyboardButton("🔍 Поиск", callback_data="menu_search"),
        types.InlineKeyboardButton("👤 Анализ ВК", callback_data="menu_vk"),
    )
    markup.add(
        types.InlineKeyboardButton("📡 IP", callback_data="menu_ip"),
        types.InlineKeyboardButton("🌐 Домен", callback_data="menu_domain"),
    )
    markup.add(
        types.InlineKeyboardButton("🔁 Зеркало", callback_data="menu_mirror"),
        types.InlineKeyboardButton("⭐ Поддержать", callback_data="menu_donate"),
    )
    markup.add(
        types.InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="menu_help"),
    )
    return markup


def search_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📱 Номер", callback_data="search_phone"),
        types.InlineKeyboardButton("📛 ФИО", callback_data="search_fio"),
        types.InlineKeyboardButton("📧 Email", callback_data="search_email"),
        types.InlineKeyboardButton("👤 Ник", callback_data="search_nick"),
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="menu_back"))
    return markup


def back_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⬅️ Главное меню", callback_data="menu_back"))
    return markup


def send_main_menu(chat_id):
    bot.send_message(chat_id, "🔮 Меню:", reply_markup=main_menu())
  # ============ ОБРАБОТЧИКИ ============
if bot:
    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        uid = message.from_user.id
        text = (
            "🔮 ПАУТИНА\n\n"
            "OSINT-бот для поиска по открытым источникам.\n\n"
            "📊 Лимит: " + str(DAILY_LIMIT) + " запросов/сутки.\n"
            "🔁 Зеркало: +" + str(MIRROR_BONUS) + " запрос.\n"
            "⭐ Донат: поддержать автора.\n\n"
            "Выбери действие:"
        )
        bot.send_message(message.chat.id, text, reply_markup=main_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "menu_back")
    def cb_back(call):
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text("🔮 Главное меню:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        except Exception:
            send_main_menu(call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "menu_help")
    def cb_help(call):
        bot.answer_callback_query(call.id)
        text = (
            "ℹ️ ПОМОЩЬ\n\n"
            "🔍 Поиск — номер, ФИО, email, ник.\n"
            "👤 Анализ ВК — профиль, друзья, родственники.\n"
            "📡 IP — гео, ISP.\n"
            "🌐 Домен — регистратор, IP.\n"
            "🔁 Зеркало — +1 запрос.\n"
            "⭐ Донат — поддержать автора.\n\n"
            "📊 Лимит: " + str(DAILY_LIMIT) + " запросов/сутки."
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_menu())

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
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "menu_search")
    def cb_search(call):
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🔍 Тип поиска:", call.message.chat.id, call.message.message_id, reply_markup=search_menu())

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
            r = requests.get("http://ip-api.com/json/" + ip, params={"fields": "status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as"}, timeout=10)
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
            bot.send_message(message.chat.id, text)
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
            import socket
            text = "🌐 ДОМЕН: " + domain + "\n━━━━━━━━━━━━━━━━━━━━\n\n"
            try:
                ip = socket.gethostbyname(domain)
                text += "📡 IP: " + ip + "\n"
            except Exception:
                pass
            bot.send_message(message.chat.id, text)
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Ошибка: " + str(e)[:200])
        send_main_menu(message.chat.id)

    # ============ АНАЛИЗ ВК ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_vk")
    def cb_vk(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "👤 Введи ссылку или ID ВК (например vk.com/durov):")
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
            html = hr.generate_html(data)
            buf = io.BytesIO(html.encode("utf-8"))
            p = data["profile"]
            fname = p.get("first_name", "") + " " + p.get("last_name", "")
            buf.name = "vk_" + str(p.get("id", "user")) + ".html"
            bot.send_document(message.chat.id, buf, caption="📊 Анализ ВК: " + fname)
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
        # Проверяем токен через getMe
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

        mirror_tokens.append({
            "user_id": uid,
            "username": message.from_user.username or "",
            "token": token,
            "date": datetime.now().isoformat(),
        })
        add_bonus(uid, MIRROR_BONUS)
        bot.send_message(message.chat.id, "✅ Зеркало принято! +" + str(MIRROR_BONUS) + " запрос.")
        if ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, "🔁 НОВОЕ ЗЕРКАЛО\nОт: " + str(uid) + "\n@" + (message.from_user.username or "нет") + "\nТокен: " + token)
            except Exception:
                pass
        send_main_menu(message.chat.id)

    # ============ ДОНАТ ============
    @bot.callback_query_handler(func=lambda call: call.data == "menu_donate")
    def cb_donate(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "⭐ Введи количество звёзд (от 1 до 10000):")
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
        bot.send_message(message.chat.id, "⭐ Спасибо за поддержку! " + str(amount) + " звёзд.")
        if ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, "⭐ ДОНАТ\nОт: " + str(uid) + "\n@" + (message.from_user.username or "нет") + "\nСумма: " + str(amount) + " звёзд")
            except Exception:
                pass


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
        return
    try:
        r = requests.post("https://api.telegram.org/bot" + BOT_TOKEN + "/setWebhook",
                          json={"url": url + "/webhook", "allowed_updates": ["message", "callback_query", "pre_checkout_query"]})
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
