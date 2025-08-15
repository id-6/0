import asyncio
import json
import os
from telethon import TelegramClient, events, types, Button, functions
from telethon.errors import SessionPasswordNeededError, FloodWaitError

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'ضع_التوكن_هنا')
D7_BOT_USERNAME = "D7Bot"
CONFIG_FILE = "userbot_config.json"
DELAY_BETWEEN_MESSAGES = 1

ADMIN_RIGHTS = types.ChatAdminRights(
    change_info=True, post_messages=True, edit_messages=True,
    delete_messages=True, ban_users=True, invite_users=True,
    pin_messages=True, add_admins=True, manage_call=True,
    other=True, anonymous=False
)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"accounts": []}, f)
            return {"accounts": []}
    return {"accounts": []}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

async def setup_account_via_bot(conv):
    await conv.send_message("📲 أرسل رقم الهاتف (مثال +96477xxxxxxx):")
    phone = (await conv.get_response()).text.strip()
    await conv.send_message("🔑 أدخل API ID:")
    api_id = int((await conv.get_response()).text.strip())
    await conv.send_message("🛡️ أدخل API HASH:")
    api_hash = (await conv.get_response()).text.strip()
    session_file = f"userbot_{phone}.session"
    client = TelegramClient(session_file, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        await conv.send_message("📩 أدخل كود التحقق:")
        code = (await conv.get_response()).text.strip()
        try: await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            await conv.send_message("🔑 أدخل كلمة مرور 2FA:")
            password = (await conv.get_response()).text.strip()
            await client.sign_in(password=password)
    config = load_config()
    if not any(acc["phone"] == phone for acc in config["accounts"]):
        config["accounts"].append({"phone": phone,"api_id": api_id,"api_hash": api_hash,"session": session_file})
        save_config(config)
    await conv.send_message(f"✅ تم تسجيل Userbot وحفظ الجلسة: {session_file}")
    await client.disconnect()

async def create_supergroup(client, title):
    result = await client(functions.channels.CreateChannelRequest(title=title, about="مرحباً بالجميع", megagroup=True))
    channel = result.chats[0]
    try:
        d7 = await client.get_entity(D7_BOT_USERNAME)
        await client(functions.channels.EditAdminRequest(channel=channel, user_id=d7, admin_rights=ADMIN_RIGHTS, rank="Admin"))
    except: pass
    for _ in range(7):
        try: await client.send_message(channel, "ايدي")
        except: pass
    print(f"[+] تم إنشاء القروب: {title}")

async def main():
    bot_client = TelegramClient("bot_session", 29885460, "9fece1c7f0ebf1526ed9ade4cb455a03")
    await bot_client.start(bot_token=BOT_TOKEN)

    @bot_client.on(events.NewMessage(pattern="/start"))
    async def start_handler(event):
        buttons = [[Button.inline("إضافة حساب جديد", b"add_account")],[Button.inline("5", b"5"), Button.inline("10", b"10")],[Button.inline("15", b"15"), Button.inline("20", b"20")],[Button.inline("30", b"30"), Button.inline("40", b"40")],[Button.inline("50", b"50")]]
        await event.respond("اختر ما تريد:", buttons=buttons)

    @bot_client.on(events.CallbackQuery)
    async def callback_handler(event):
        async with bot_client.conversation(event.sender_id) as conv:
            if event.data == b"add_account":
                await setup_account_via_bot(conv)
                await event.answer("✅ تم إضافة الحساب!")
            elif event.data.decode() in ["5","10","15","20","30","40","50"]:
                count = int(event.data.decode())
                config = load_config()
                if not config["accounts"]:
                    await conv.send_message("❌ سجل دخول Userbot أولاً.")
                    return
                account = config["accounts"][-1]
                client = TelegramClient(account["session"], account["api_id"], account["api_hash"])
                await client.start(phone=account["phone"])
                for i in range(1, count+1):
                    await create_supergroup(client, f"Group #{i}")
                    await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
                await conv.send_message(f"[+] تم إنشاء {count} مجموعات وإرسال 7 رسائل 'ايدي' لكل مجموعة!")
                await client.disconnect()

    print("[*] البوت جاهز! ارسل /start في تليجرام.")
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
