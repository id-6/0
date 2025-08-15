import asyncio
import json
import os
from telethon import TelegramClient, events, types, Button, functions
from telethon.errors import SessionPasswordNeededError, FloodWaitError

# ===== الإعدادات =====
BOT_TOKEN = "5876070267:AAEN89CArFut-2ObR2BpbT5Oq4QhQQX3Jww"
D7_BOT_USERNAME = "D7Bot"
CONFIG_FILE = "userbot_config.json"

# ===== إعدادات الوقت =====
DELAY_BETWEEN_MESSAGES = 1  # ثواني بين كل رسالة "ايدي"
MAX_CONCURRENT_GROUPS = 5   # عدد القروبات المتوازية في نفس الوقت

ADMIN_RIGHTS = types.ChatAdminRights(
    change_info=True,
    post_messages=True,
    edit_messages=True,
    delete_messages=True,
    ban_users=True,
    invite_users=True,
    pin_messages=True,
    add_admins=True,
    manage_call=True,
    other=True,
    anonymous=False
)

# ===== حفظ واسترجاع إعدادات Userbot =====
def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"accounts": []}

# ===== تسجيل حساب جديد =====
async def setup_account_via_bot(conv):
    await conv.send_message("📲 أرسل رقم الهاتف (مثال +96477xxxxxxx):")
    msg = await conv.get_response()
    phone = msg.text.strip()

    await conv.send_message("🔑 أدخل API ID:")
    msg = await conv.get_response()
    api_id = int(msg.text.strip())

    await conv.send_message("🛡️ أدخل API HASH:")
    msg = await conv.get_response()
    api_hash = msg.text.strip()

    session_file = f"userbot_{phone}.session"
    client = TelegramClient(session_file, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        await conv.send_message("📩 أدخل كود التحقق المرسل لك:")
        code_msg = await conv.get_response()
        code = code_msg.text.strip()
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            await conv.send_message("🔑 أدخل كلمة المرور 2FA:")
            pwd_msg = await conv.get_response()
            password = pwd_msg.text.strip()
            await client.sign_in(password=password)

    # حفظ الحساب إذا غير موجود
    config = load_config()
    if not any(acc["phone"] == phone for acc in config["accounts"]):
        config["accounts"].append({
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash,
            "session": session_file
        })
        save_config(config)
    await conv.send_message(f"✅ تم تسجيل Userbot وحفظ الجلسة: {session_file}")
    await client.disconnect()

# ===== إنشاء قروب =====
async def create_supergroup(client, title):
    try:
        result = await client(functions.channels.CreateChannelRequest(
            title=title,
            about="مرحباً بالجميع",
            megagroup=True
        ))
        channel = result.chats[0]

        # إضافة D7Bot كأدمن
        try:
            d7 = await client.get_entity(D7_BOT_USERNAME)
            await client(functions.channels.EditAdminRequest(
                channel=channel,
                user_id=d7,
                admin_rights=ADMIN_RIGHTS,
                rank="Admin"
            ))
        except Exception as e:
            print(f"[!] خطأ إضافة @{D7_BOT_USERNAME} كأدمن: {e}")

        # إرسال 7 رسائل "ايدي" مع تأخير
        for _ in range(7):
            try:
                await client.send_message(channel, "ايدي")
                await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
            except FloodWaitError as e:
                print(f"[!] FloodWait، انتظر {e.seconds} ثانية")
                await asyncio.sleep(e.seconds)
                await client.send_message(channel, "ايدي")

        print(f"[+] تم إنشاء القروب: {title}")

    except FloodWaitError as e:
        print(f"[!] FloodWait عند إنشاء القروب {title}, انتظر {e.seconds} ثانية")
        await asyncio.sleep(e.seconds)
        await create_supergroup(client, title)

# ===== Main =====
async def main():
    bot_client = TelegramClient("bot_session", 29885460, "9fece1c7f0ebf1526ed9ade4cb455a03")
    await bot_client.start(bot_token=BOT_TOKEN)

    @bot_client.on(events.NewMessage(pattern="/start"))
    async def start_handler(event):
        config = load_config()
        buttons = [[Button.inline("إضافة حساب جديد", b"add_account")]]
        # لكل حساب موجود أزرار لاختياره
        for acc in config["accounts"]:
            buttons.append([Button.inline(acc["phone"], f"account_{acc['phone']}".encode())])
        # خيارات عدد القروبات
        buttons.append([
            Button.inline("5", b"5"), Button.inline("10", b"10"),
            Button.inline("20", b"20"), Button.inline("30", b"30"),
            Button.inline("40", b"40"), Button.inline("50", b"50")
        ])
        await event.respond("اختر الحساب وعدد القروبات:", buttons=buttons)

    selected_account = {}

    @bot_client.on(events.CallbackQuery)
    async def callback_handler(event):
        nonlocal selected_account
        async with bot_client.conversation(event.sender_id) as conv:
            data = event.data.decode()
            if data == "add_account":
                await setup_account_via_bot(conv)
                await event.answer("✅ تم إضافة الحساب!")

            elif data.startswith("account_"):
                phone = data.split("_", 1)[1]
                config = load_config()
                selected_account[event.sender_id] = next(acc for acc in config["accounts"] if acc["phone"] == phone)
                await conv.send_message(f"✅ تم اختيار الحساب: {phone}")

            elif data in ["5", "10", "20", "30", "40", "50"]:
                count = int(data)
                if event.sender_id not in selected_account:
                    await conv.send_message("❌ حدد أولاً الحساب الذي تريد استخدامه.")
                    return
                account = selected_account[event.sender_id]
                client = TelegramClient(account["session"], account["api_id"], account["api_hash"])
                await client.start(phone=account["phone"])

                # تقسيم القروبات لمجموعات متوازية
                groups = [f"Group #{i}" for i in range(1, count + 1)]
                for i in range(0, len(groups), MAX_CONCURRENT_GROUPS):
                    batch = groups[i:i+MAX_CONCURRENT_GROUPS]
                    tasks = [create_supergroup(client, title) for title in batch]
                    await asyncio.gather(*tasks)

                await conv.send_message(f"[+] تم إنشاء {count} مجموعات باستخدام الحساب {account['phone']}")
                await client.disconnect()

    print("[*] البوت جاهز! ارسل /start في تليجرام.")
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
