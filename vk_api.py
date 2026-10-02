#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import requests

VK_TOKEN = os.environ.get("VK_TOKEN", "")
VK_VERSION = "5.199"
VK_API = "https://api.vk.com/method/"


def vk_call(method, params=None, retries=3):
    if not VK_TOKEN:
        return {"error": "VK_TOKEN не задан"}
    params = params or {}
    params["access_token"] = VK_TOKEN
    params["v"] = VK_VERSION
    for attempt in range(retries):
        try:
            r = requests.get(VK_API + method, params=params, timeout=15)
            data = r.json()
            if "error" in data:
                code = data["error"].get("error_code")
                if code == 6:
                    time.sleep(1)
                    continue
                return data
            return data
        except Exception as e:
            if attempt == retries - 1:
                return {"error": str(e)}
            time.sleep(1)
    return {"error": "unknown"}


def get_user(user_id):
    fields = "photo_200,photo_max_orig,city,bdate,status,sex,relation,site,education,universities,schools,career,counters,followers_count,last_seen,online,about,activities,interests,music,movies,books,games"
    data = vk_call("users.get", {"user_ids": user_id, "fields": fields})
    if "error" in data or not data.get("response"):
        return None
    return data["response"][0]


def get_users(user_ids):
    if not user_ids:
        return []
    fields = "photo_100,city,bdate,last_name,first_name"
    result = []
    for i in range(0, len(user_ids), 1000):
        chunk = user_ids[i:i + 1000]
        data = vk_call("users.get", {"user_ids": ",".join(str(x) for x in chunk), "fields": fields})
        if "response" in data:
            result.extend(data["response"])
    return result


def get_friends(user_id):
    data = vk_call("friends.get", {"user_id": user_id, "count": 5000})
    if "error" in data:
        return []
    return data.get("response", {}).get("items", [])


def get_groups(user_id):
    data = vk_call("groups.get", {"user_id": user_id, "count": 1000, "extended": 1, "fields": "name"})
    if "error" in data:
        return []
    return data.get("response", {}).get("items", [])


def get_photos(user_id):
    data = vk_call("photos.get", {"owner_id": user_id, "album_id": "profile", "count": 200})
    if "error" in data:
        return []
    return data.get("response", {}).get("items", [])


def get_wall(user_id):
    data = vk_call("wall.get", {"owner_id": user_id, "count": 100})
    if "error" in data:
        return []
    return data.get("response", {}).get("items", [])
