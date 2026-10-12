"""One-time login of the spare Telegram account.   python login.py

Asks for the phone number, the code Telegram sends to the app, and the 2FA password if any. Prints the
TELEGRAM_SESSION line for .env and lists the channels/groups of the account (the names for settings.py).
Use a separate login for the server: never use the same session string in two places at once.
"""
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

from settings import require


async def main() -> None:
    client = TelegramClient(StringSession(), int(require("API_ID")), require("API_HASH"))
    await client.start()
    print("\nPut this line in your .env (keep it secret, it gives full access to the account):")
    print(f"TELEGRAM_SESSION={client.session.save()}")
    print("\nChannels and groups of this account (copy the right-hand value into CHANNELS in settings.py):")
    async for d in client.iter_dialogs():
        if d.is_channel or d.is_group:
            username = getattr(d.entity, "username", None)
            print(f"{d.name[:45]:45} -> {repr('@' + username) if username else d.id}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
