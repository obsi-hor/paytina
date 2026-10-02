#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import vk_api as vk


def extract_vk_id(text):
    text = text.strip()
    m = re.search(r"vk\.com/id(\d+)", text)
    if m:
        return m.group(1)
    m = re.search(r"vk\.com/([a-zA-Z0-9_\.]+)", text)
    if m:
        return m.group(1)
    m = re.search(r"^id(\d+)$", text)
    if m:
        return m.group(1)
    return text


def find_relatives(target_fio, friends_data):
    if not target_fio:
        return []
    parts = target_fio.split()
    target_lastname = parts[0].lower() if parts else ""
    if not target_lastname:
        return []
    relatives = []
    for f in friends_data:
        last = (f.get("last_name") or "").lower()
        if last == target_lastname:
            relatives.append({
                "id": f.get("id"),
                "name": (f.get("first_name") or "") + " " + (f.get("last_name") or ""),
                "last_name": f.get("last_name"),
                "city": (f.get("city") or {}).get("title") if isinstance(f.get("city"), dict) else None,
                "bdate": f.get("bdate"),
                "photo": f.get("photo_100"),
            })
    return relatives


def analyze_vk(user_input):
    vk_id = extract_vk_id(user_input)
    profile = vk.get_user(vk_id)
    if not profile:
        return None
    user_id = profile.get("id")
    result = {
        "profile": profile,
        "friends": [],
        "friends_total": 0,
        "relatives": [],
        "groups": [],
        "photos_count": 0,
        "wall_count": 0,
    }
    friends_ids = vk.get_friends(user_id)
    if friends_ids:
        friends_data = vk.get_users(friends_ids[:1000])
        result["friends"] = friends_data
        result["friends_total"] = len(friends_ids)
        fio = (profile.get("first_name", "") + " " + profile.get("last_name", "")).strip()
        result["relatives"] = find_relatives(fio, friends_data)
    result["groups"] = vk.get_groups(user_id)[:50]
    result["photos_count"] = len(vk.get_photos(user_id))
    result["wall_count"] = len(vk.get_wall(user_id))
    return result
