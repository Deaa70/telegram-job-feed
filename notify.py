"""Posts the matches to your private Telegram channel through your bot (Bot API over HTTPS)."""
import html
import json
import re
import time

import httpx

import db
from settings import log, require

SECONDS_BETWEEN_MESSAGES = 3   # Telegram allows about 20 messages per minute into one chat
MAX_VISIBLE_CHARS = 3800       # Telegram's limit is 4096 visible characters
CONFIG_ERRORS = ("chat not found", "administrator", "not enough rights", "no rights", "not a member", "kicked")



JOB_TYPE_AR = {
    "full-time": "دوام كامل",
    "part-time": "دوام جزئي",
    "contract": "عقد",
    "freelance": "عمل حر",
    "internship": "تدريب",
}
WORK_MODE_AR = {
    "remote": "عن بعد",
    "hybrid": "هجين",
    "on-site": "حضوري",
}
GENDER_AR = {
    "male": "ذكر",
    "female": "أنثى",
    "any": "ذكر أو أنثى",
}

class TelegramError(RuntimeError):
    def __init__(self, status: int, text: str):
        super().__init__(f"Telegram error {status}: {text[:200]}")
        self.status = status


def api(token: str, method: str, payload: dict) -> dict:
    """One Bot API call. Waits and retries once if Telegram says 'too many requests'."""
    for attempt in (1, 2):
        r = httpx.post(f"https://api.telegram.org/bot{token}/{method}", json=payload, timeout=30)
        if r.status_code == 429 and attempt == 1:
            time.sleep(r.json().get("parameters", {}).get("retry_after", 5) + 1)
            continue
        if r.status_code >= 400:
            raise TelegramError(r.status_code, r.text)
        return r.json()


# ------------------------------------------------------------------ message layout

def esc(value) -> str:
    return html.escape(str(value), quote=False)


def to_plain(text: str) -> str:
    return html.unescape(re.sub(r"</?b>", "", text))


def bullets(items) -> str:
    return "\n".join(f"• {esc(i)}" for i in items)


def format_message(row) -> str:
    """Telegram HTML. Arabic labels, Arabic descriptive text, tech terms stay in English."""
    d = json.loads(row["details"])

    blocks = {
        "head": (
            f"<b>{esc(d.get('title') or 'وظيفة')}</b>\n"
            f"🏢 <b>{esc(d.get('company') or 'الشركة غير مذكورة')}</b>"
        )
    }

    facts = []

    place = ", ".join(x for x in (d.get("city"), d.get("country")) if x)
    work_mode = WORK_MODE_AR.get(d.get("work_mode"), d.get("work_mode")) if d.get("work_mode") else ""
    where = " · ".join(
        x for x in (
            f"<b>{esc(place)}</b>" if place else "",
            esc(work_mode) if work_mode else "",
        ) if x
    )
    if where:
        facts.append(f"📍 {where}")

    if d.get("visa"):
        facts.append(f"🛂 {esc(d['visa'])}")

    if d.get("job_type"):
        facts.append(f"💼 {esc(JOB_TYPE_AR.get(d['job_type'], d['job_type']))}")

    if d.get("working_hours"):
        facts.append(f"⏱ <b>ساعات العمل:</b> {esc(d['working_hours'])}")

    if d.get("duration"):
        facts.append(f"📆 <b>المدة:</b> {esc(d['duration'])}")

    gender = GENDER_AR.get(d.get("gender"), "غير محدد")
    facts.append(f"👥 <b>الجنس:</b> {gender}")

    if d.get("salary"):
        facts.append(f"💰 <b>الراتب:</b> {esc(d['salary'])}")

    if d.get("deadline"):
        facts.append(f"📅 <b>آخر موعد للتقديم:</b> {esc(d['deadline'])}")

    blocks["facts"] = "\n".join(facts)

    if d.get("summary"):
        blocks["about"] = f"📝 <b>نبذة</b>\n{esc(d['summary'])}"

    if d.get("positions"):
        blocks["positions"] = f"🧩 <b>الوظائف</b>\n{bullets(d['positions'])}"

    if d.get("responsibilities"):
        blocks["resp"] = f"✅ <b>المسؤوليات</b>\n{bullets(d['responsibilities'])}"

    if d.get("requirements"):
        blocks["req"] = f"📋 <b>المتطلبات</b>\n{bullets(d['requirements'])}"

    if d.get("stack"):
        blocks["stack"] = f"🛠 <b>التقنيات:</b> {esc(', '.join(d['stack']))}"

    if d.get("benefits"):
        blocks["benefits"] = f"🎁 <b>المزايا</b>\n{bullets(d['benefits'])}"

    contacts = d.get("contacts") or {}
    lines = [
        f"{icon} {esc(v)}"
        for key, icon in (
            ("phones", "📱"),
            ("emails", "✉️"),
            ("handles", "💬"),
            ("links", "🔗"),
        )
        for v in contacts.get(key) or []
    ]
    if lines:
        blocks["contact"] = "📞 <b>التواصل</b>\n" + "\n".join(lines)

    for name in ("benefits", "resp", "about"):
        if len(to_plain("\n\n".join(blocks.values()))) <= MAX_VISIBLE_CHARS:
            break
        blocks.pop(name, None)

    return "\n\n".join(blocks.values())
# ------------------------------------------------------------------ sending

def send_one(token, chat_id, row) -> None:
    """HTML + button; if Telegram refuses (400), retry without the button, then as plain text."""
    text = format_message(row)
    base = {"chat_id": chat_id, "disable_web_page_preview": True}
    variants = [{**base, "text": text, "parse_mode": "HTML"}, {**base, "text": to_plain(text)}]
    # if row["link"]:
    #     button = {"inline_keyboard": [[{"text": "Open post", "url": row["link"]}]]}
    #     variants.insert(0, {**variants[0], "reply_markup": button})
    for i, payload in enumerate(variants):
        try:
            api(token, "sendMessage", payload)
            return
        except TelegramError as e:
            if e.status != 400 or i == len(variants) - 1:
                raise


def send_all(conn) -> int:
    rows = db.posts(conn, "match")
    if not rows:
        log("  nothing to send")
        return 0
    token, chat_id = require("BOT_TOKEN"), require("NOTIFY_CHAT_ID")
    sent = network_failures = 0
    for r in rows:
        try:
            send_one(token, chat_id, r)
            db.set_status(conn, r["id"], "sent")
            sent += 1
            network_failures = 0
            log(f"  sent post {r['id']}")
            time.sleep(SECONDS_BETWEEN_MESSAGES)
        except TelegramError as e:
            if e.status in (401, 403, 404) or any(h in str(e).lower() for h in CONFIG_ERRORS):
                raise SystemExit(f"{e}. Check BOT_TOKEN and NOTIFY_CHAT_ID, and that the bot is an admin of the channel with "
                                 "the 'Post messages' permission.")
            if 400 <= e.status < 500:  # Telegram refuses this very post: give up on it, never retry
                db.set_status(conn, r["id"], "failed")
                log(f"  post {r['id']} refused by Telegram, marked failed: {e}")
            else:
                network_failures += 1
                log(f"  post {r['id']} not sent ({e}); retried on the next run")
        except httpx.HTTPError as e:
            network_failures += 1
            log(f"  post {r['id']} not sent ({e}); retried on the next run")
        if network_failures >= 3:
            log("  3 failures in a row, stopping; the rest is sent on the next run")
            break
    return sent


def alert(text: str) -> None:
    """Best-effort message to the channel when a run fails. Never raises."""
    try:
        api(require("BOT_TOKEN"), "sendMessage", {"chat_id": require("NOTIFY_CHAT_ID"), "text": text[:4000]})
    except BaseException:
        pass
