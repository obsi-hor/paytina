#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, parse_qs

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


def _clean_url(url):
    if not url:
        return None
    if url.startswith("//duckduckgo.com/l/?"):
        parsed = urlparse("https:" + url)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    if url.startswith("/l/?"):
        parsed = urlparse("https://duckduckgo.com" + url)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return url


def search(query, max_results=10):
    results = []
    try:
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "ru-ru"},
            headers=HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            return results
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select(".result")[:max_results]:
            link_el = item.select_one(".result__a")
            if not link_el:
                continue
            title = link_el.get_text(strip=True)
            url = _clean_url(link_el.get("href"))
            snippet_el = item.select_one(".result__snippet")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            if url:
                results.append({"title": title, "url": url, "snippet": snippet})
    except Exception as e:
        print("[ERROR] ddg.search: " + str(e))
    return results


def multi_search(queries, max_per=2):
    seen = set()
    out = []
    for q in queries:
        for r in search(q, max_results=max_per):
            if r["url"] not in seen:
                seen.add(r["url"])
                out.append(r)
    return out


def format_results(results, limit=15):
    if not results:
        return "❌ Ничего не найдено в открытых источниках.\n"
    text = ""
    for i, r in enumerate(results[:limit], 1):
        text += str(i) + ". " + r["title"][:80] + "\n"
        text += "   🔗 " + r["url"][:100] + "\n"
        if r.get("snippet"):
            text += "   📝 " + r["snippet"][:150] + "\n"
        text += "\n"
    return text
