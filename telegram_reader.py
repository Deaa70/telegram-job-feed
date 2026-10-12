"""Reads the latest posts of your channels with a normal Telegram user account (Telethon). Read-only."""
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession

import db
from settings import CHANNELS, LOOKBACK_HOURS, MAX_PER_CHANNEL, MIN_CHARS, log, require


def post_link(entity, msg_id):
    username = getattr(entity, "username", None)
    if username:
        return f"https://t.me/{username}/{msg_id}"
    return f"https://t.me/c/{entity.id}/{msg_id}" if getattr(entity, "id", None) else None


def hidden_links(m) -> list:
    """Links that are not visible in the text: hyperlinks behind words and inline-button URLs.
    Many job channels put the apply link there."""
    urls = []
    try:
        for ent in getattr(m, "entities", None) or []:
            if getattr(ent, "url", None):
                urls.append(ent.url)
        for row in getattr(m, "buttons", None) or []:
            for button in row:
                if getattr(button, "url", None):
                    urls.append(button.url)
    except Exception:
        pass
    return list(dict.fromkeys(urls))


async def fetch_channel(client, conn, ref, cutoff) -> int:
    try:
        entity = await client.get_entity(ref)
    except Exception as e:
        log(f"  {ref}: cannot open it ({e}). Is the spare account a member? Skipping.")
        return 0
    saved = read = 0
    async for m in client.iter_messages(entity, limit=MAX_PER_CHANNEL):  # newest first
        if m.date < cutoff:
            break
        read += 1
        text = (m.raw_text or "").strip()
        if len(text) >= MIN_CHARS and db.add_post(conn, str(ref), m.id, text, post_link(entity, m.id), hidden_links(m)):
            saved += 1
    log(f"  {ref}: {read} post(s) in the last {LOOKBACK_HOURS}h, {saved} new")
    return saved


async def fetch(conn) -> int:
    client = TelegramClient(StringSession(require("TELEGRAM_SESSION")), int(require("API_ID")), require("API_HASH"))
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise SystemExit("The Telegram session is not valid anymore. Run `python login.py` and update TELEGRAM_SESSION.")
        await client.get_dialogs()  # lets numeric ids of private channels resolve
        cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
        return sum([await fetch_channel(client, conn, ref, cutoff) for ref in CHANNELS])
    finally:
        await client.disconnect()