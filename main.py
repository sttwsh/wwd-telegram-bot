import os
import time
import json
import feedparser
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

STATE_FILE = "state.json"

# RSS WWD (можно потом добавить больше)
FEEDS = [
    "https://wwd.com/feed/"
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
    return entry.get("id") or entry.get("link")

def format_post(entry):
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    summary = entry.get("summary", "").strip()

    text = f"📰 <b>{title}</b>\n\n"
    if summary:
        text += summary[:300].replace("\n", " ") + "\n\n"
    text += link
    return text

def job():
    if not BOT_TOKEN or not CHANNEL_ID:
        return

    bot = Bot(token=BOT_TOKEN)
    state = load_state()
    posted = set(state.get("posted", []))

    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in reversed(feed.entries):
            eid = entry_id(entry)
            if not eid or eid in posted:
                continue

            bot.send_message(
                chat_id=CHANNEL_ID,
                text=format_post(entry),
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            posted.add(eid)
            time.sleep(1.5)

    state["posted"] = list(posted)[-2000:]
    save_state(state)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", minutes=15)
    scheduler.start()
