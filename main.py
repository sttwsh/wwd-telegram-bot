import os
import json
import asyncio
import time
import feedparser
from telegram import Bot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

STATE_FILE = "state.json"

# RSS WWD (можно потом добавить больше)
FEEDS = [
    "https://wwd.com/feed/",
]

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"posted": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def entry_id(entry):
    return entry.get("id") or entry.get("guid") or entry.get("link")

def format_post(entry):
    title = (entry.get("title") or "").strip()
    link = (entry.get("link") or "").strip()
    summary = (entry.get("summary") or "").strip()

    text = f"📰 <b>{title}</b>\n\n"
    if summary:
        text += summary[:300].replace("\n", " ") + "\n\n"
    text += link
    return text

async def run_once():
    if not BOT_TOKEN or not CHANNEL_ID:
        raise RuntimeError("Не заданы BOT_TOKEN или CHANNEL_ID в Secrets.")

    bot = Bot(token=BOT_TOKEN)

    state = load_state()
    posted = set(state.get("posted", []))

    new_count = 0

    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)

        # идём от старых к новым, чтобы красиво постилось по порядку
        for entry in reversed(getattr(feed, "entries", [])):
            eid = entry_id(entry)
            if not eid or eid in posted:
                continue

            text = format_post(entry)

            # ВАЖНО: await (иначе твоя текущая ошибка)
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            posted.add(eid)
            new_count += 1

            # лёгкая пауза, чтобы не упереться в лимиты
            await asyncio.sleep(1.2)

    state["posted"] = list(posted)[-2000:]
    save_state(state)

    print(f"Posted: {new_count}")

def main():
    asyncio.run(run_once())

if __name__ == "__main__":
    main()
