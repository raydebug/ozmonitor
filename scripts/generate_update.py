from __future__ import annotations

import json
import pathlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LATEST_PATH = DATA_DIR / "latest.json"
HISTORY_PATH = DATA_DIR / "history.json"


def now_aest() -> datetime:
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo("Australia/Brisbane"))
    return datetime.now(timezone.utc)


def fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ozmonitor-lite/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any]:
    return json.loads(fetch_text(url, timeout=timeout))


def parse_rss_items(rss_text: str, limit: int = 6) -> list[dict[str, str]]:
    root = ET.fromstring(rss_text)
    items: list[dict[str, str]] = []
    for node in root.findall(".//item")[:limit]:
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        desc = (node.findtext("description") or "").strip()
        pub = (node.findtext("pubDate") or "").strip()
        time_str = ""
        if pub:
            try:
                dt = parsedate_to_datetime(pub)
                if dt.tzinfo and ZoneInfo is not None:
                    dt = dt.astimezone(ZoneInfo("Australia/Brisbane"))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                time_str = pub
        items.append(
            {
                "title": title,
                "url": link,
                "description": desc,
                "time": time_str,
                "type": "news",
            }
        )
    return items


def get_news_events() -> tuple[list[dict[str, str]], str]:
    # ABC top stories RSS
    rss_url = "https://www.abc.net.au/news/feed/51120/rss.xml"
    text = fetch_text(rss_url)
    items = parse_rss_items(text, limit=8)
    return items, ""


def get_weather_event() -> tuple[dict[str, str], str]:
    params = urllib.parse.urlencode(
        {
            "latitude": -27.47,
            "longitude": 153.02,
            "current": "temperature_2m,wind_speed_10m",
            "timezone": "Australia/Brisbane",
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    data = fetch_json(url)
    current = data.get("current", {})
    temp = current.get("temperature_2m")
    wind = current.get("wind_speed_10m")
    units = data.get("current_units", {})
    temp_u = units.get("temperature_2m", "C")
    wind_u = units.get("wind_speed_10m", "km/h")
    item = {
        "title": "Brisbane Weather",
        "description": f"Temperature {temp}{temp_u}, Wind {wind}{wind_u}",
        "time": (current.get("time") or "").replace("T", " "),
        "type": "weather",
        "url": "",
    }
    return item, ""


def get_fx_event() -> tuple[dict[str, str], str, str]:
    data = fetch_json("https://open.er-api.com/v6/latest/AUD")
    usd = data.get("rates", {}).get("USD")
    timestamp = data.get("time_last_update_utc", "")
    item = {
        "title": "AUD/USD",
        "description": f"1 AUD = {usd} USD",
        "time": timestamp,
        "type": "market",
        "url": "https://open.er-api.com/",
    }
    return item, "", f"{usd}"


def trim_text(text: str, max_len: int = 140) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def build_payload() -> dict[str, Any]:
    errors: list[str] = []
    events: list[dict[str, str]] = []
    stats: dict[str, str] = {}

    try:
        news, err = get_news_events()
        if err:
            errors.append(err)
        events.extend(news[:5])
        stats["News Items"] = str(len(news))
    except Exception as ex:
        errors.append(f"news: {ex}")
        stats["News Items"] = "0"

    temp_val = "N/A"
    try:
        weather_event, err = get_weather_event()
        if err:
            errors.append(err)
        events.insert(0, weather_event)
        desc = weather_event.get("description", "")
        temp_val = desc.split(",")[0].replace("Temperature ", "") if desc else "N/A"
    except Exception as ex:
        errors.append(f"weather: {ex}")

    fx_val = "N/A"
    try:
        fx_event, err, fx_val = get_fx_event()
        if err:
            errors.append(err)
        events.insert(1, fx_event)
    except Exception as ex:
        errors.append(f"fx: {ex}")

    stats["Brisbane Temp"] = temp_val
    stats["AUD/USD"] = fx_val
    stats["Errors"] = str(len(errors))

    now = now_aest()
    summary = [
        f"监控时间: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"新闻抓取数量: {stats['News Items']}",
        f"布里斯班温度: {stats['Brisbane Temp']}",
        f"AUD/USD: {stats['AUD/USD']}",
    ]
    if errors:
        summary.append("异常: " + "; ".join(trim_text(e, 90) for e in errors))

    for item in events:
        item["description"] = trim_text(item.get("description", ""), 180)

    return {
        "updated_at": now.isoformat(),
        "stats": stats,
        "summary": summary,
        "events": events,
    }


def update_history(latest: dict[str, Any]) -> list[dict[str, Any]]:
    if HISTORY_PATH.exists():
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    else:
        history = []
    history.append(
        {
            "updated_at": latest.get("updated_at"),
            "stats": latest.get("stats", {}),
        }
    )
    return history[-300:]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    latest = build_payload()
    history = update_history(latest)
    LATEST_PATH.write_text(
        json.dumps(latest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    HISTORY_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("updated:", LATEST_PATH)


if __name__ == "__main__":
    main()
