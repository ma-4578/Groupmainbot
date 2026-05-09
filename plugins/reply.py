import os
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

# --- Database Setup ---
MONGO_URL = os.environ.get("MONGO_URL", "")
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Khh_db"]
replies = db["auto_replies_v2"]

OWNER_ID = int(os.environ.get("OWNER_ID", 0))

@Client.on_message(filters.group & ~filters.bot)
async def auto_learn_and_reply(client: Client, message: Message):
    
    # ၁။ စာသင်ယူခြင်း (Reply ထောက်ထားလျှင်)
    if message.reply_to_message:
        reply_to = message.reply_to_message
        
        if reply_to.from_user and reply_to.from_user.is_bot:
            return

        trigger = None
        # အမေးစာသား/Sticker
        if reply_to.text:
            trigger = reply_to.text.lower().strip()
        elif reply_to.sticker:
            trigger = reply_to.sticker.file_unique_id

        reply_data = None
        reply_type = None
        # အဖြေစာသား/Sticker
        if message.text:
            reply_data = message.text
            reply_type = "text"
        elif message.sticker:
            reply_data = message.sticker.file_id
            reply_type = "sticker"

        if trigger and reply_data:
            # မှတ်သားခြင်း
            exists = await replies.find_one({"trigger": trigger, "reply": reply_data})
            if not exists:
                await replies.insert_one({
                    "trigger": trigger,
                    "reply": reply_data,
                    "reply_type": reply_type
                })
                print(f"✅ Learned: {trigger} -> {reply_data}")
            return # စာသင်ပြီးရင် ပြန်မဖြေခိုင်းတော့ဘူး

    # ၂။ အလိုအလျောက် ပြန်ဖြေခြင်း
    current_trigger = None
    if message.text:
        current_trigger = message.text.lower().strip()
    elif message.sticker:
        current_trigger = message.sticker.file_unique_id

    if current_trigger:
        cursor = replies.find({"trigger": current_trigger})
        all_replies = await cursor.to_list(length=50)

        if all_replies:
            found = random.choice(all_replies)
            if found["reply_type"] == "text":
                await message.reply_text(found["reply"])
            else:
                await message.reply_sticker(found["reply"])
