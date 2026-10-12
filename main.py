"""Run once a day:   python main.py

read channels -> filter tech jobs (LLM) -> extract details (LLM) -> post to your Telegram channel
"""
import asyncio
import time

import db
import llm
import notify
import telegram_reader
from settings import log


def main() -> None:
    started = time.time()
    conn = db.connect()
    log("1/4 Reading the channels")
    asyncio.run(telegram_reader.fetch(conn))
    log("2/4 Filtering tech jobs")
    llm.filter_posts(conn)
    log("3/4 Extracting the details")
    llm.extract_details(conn)
    log("4/4 Posting to your channel")
    sent = notify.send_all(conn)
    log(f"Done in {time.time() - started:.0f}s. {sent} job(s) posted. Totals: {db.counts(conn)}")


if __name__ == "__main__":
    try:
        main()
    except (Exception, SystemExit) as e:
        notify.alert(f"Job feed run failed: {e}")
        raise