#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from phonenumbers import parse, is_valid_number, carrier, geocoder, number_type
from phonenumbers import timezone as phtz

HEADERS = {"User-Agent": "Mozilla/5.0"}


def check_validity(phone):
    try:
        p = parse(phone, None)
        if not is_valid_number(p):
            return None
        return {
            "e164": "+" + str(p.country_code) + str(p.national_number),
            "operator": carrier.name_for_number(p, "ru") or carrier.name_for_number(p, "en"),
            "region": geocoder.description_for_number(p, "ru") or geocoder.description_for_number(p, "en"),
            "type": str(number_type(p)),
            "timezone": list(phtz.time_zones_for_number(p)),
        }
    except Exception:
        return None


def check_telegram(phone):
    link = "https://t.me/+" + re.sub(r"[^\d]", "", phone)
    try:
        r = requests.get(link, headers=HEADERS, timeout=10)
        if "tgme_page_title" in r.text:
            m = re.search(r'<div class="tgme_page_title"[^>]*>([^<]+)</div>', r.text)
            return {"found": True, "name": m.group(1).strip() if m else "есть", "link": link}
    except Exception:
        pass
    return {"found": False, "link": link}


def check_whatsapp(phone):
    link = "https://wa.me/" + re.sub(r"[^\d]", "", phone)
    try:
        r = requests.get(link, headers=HEADERS, timeout=10)
        return {"found": "WhatsApp" in r.text and "not on WhatsApp" not in r.text, "link": link}
    except Exception:
        pass
    return {"found": False, "link": link}


def build_queries(phone):
    num = re.sub(r"[^\d]", "", phone)
    return [
        '"' + phone + '"',
        '"' + num + '"',
        '"' + phone + '" объявление',
        '"' + phone + '" утечка',
        '"' + phone + '" telegram',
        '"' + phone + '" whatsapp',
        'site:vk.com "' + phone + '"',
        'site:ok.ru "' + phone + '"',
        'site:avito.ru "' + phone + '"',
        'site:youla.ru "' + phone + '"',
        'site:2gis.ru "' + phone + '"',
        'site:pastebin.com "' + phone + '"',
        'site:t.me "' + phone + '"',
        '"' + phone + '" работа',
        '"' + phone + '" резюме',
        '"' + phone + '" ИНН',
        '"' + phone + '" адрес',
        '"' + phone + '" суд',
    ]


def build_dorks(phone):
    return [
        'site:vk.com "' + phone + '"',
        'site:ok.ru "' + phone + '"',
        'site:avito.ru "' + phone + '"',
        'site:youla.ru "' + phone + '"',
        'site:2gis.ru "' + phone + '"',
        'site:pastebin.com "' + phone + '"',
        'site:github.com "' + phone + '"',
        'site:t.me "' + phone + '"',
        '"' + phone + '" утечка',
        '"' + phone + '" leak',
        '"' + phone + '" объявление',
        '"' + phone + '" работа',
        '"' + phone + '" резюме',
        '"' + phone + '" ИНН',
        '"' + phone + '" адрес',
    ]
