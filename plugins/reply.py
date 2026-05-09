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
    
    # ၁။ စာသင်ယူခြင်း (Reply ထောက်ထားရင်)
    if message.reply_to_message:
        reply_to = message.reply_to_message
        
        # Bot ရဲ့စာကို Reply ပြန်ရင် မမှတ်ဘူး
        if reply_to.from_user and reply_to.from_user.is_bot:
            return

        trigger = None
        if reply_to.text:
            trigger = reply_to.text.lower().strip()
        elif reply_to.sticker:
            trigger = reply_to.sticker.file_unique_id

        reply_data = None
        reply_type = None
        if message.text:
            reply_data = message.text
            reply_type = "text"
        elif message.sticker:
            reply_data = message.sticker.file_id
            reply_type = "sticker"

        if trigger and reply_data:
            print(f"DEBUG: Learning - Trigger: {trigger}, Reply: {reply_data}") # Railway log မှာ ကြည့်ဖို့
            
            exists = await replies.find_one({"trigger": trigger, "reply": reply_data})
            if not exists:
                await replies.insert_one({
                    "trigger": trigger,
                    "reply": reply_data,
                    "reply_type": reply_type
                })
                try:
                    await message.reply_text(f"✅ မှတ်သားပြီးပါပြီ")
                    await message.add_reaction("👍")
                except Exception as e:
                    print(f"DEBUG: Error adding reaction: {e}")
            return

    # ၂။ အလိုအလျောက် ပြန်ဖြေခြင်း
    else:
        current_trigger = None
        if message.text:
            current_trigger = message.text.lower().strip()
        elif message.sticker:
            current_trigger = message.sticker.file_unique_id

        if current_trigger:
            cursor = replies.find({"trigger": current_trigger})
            all_replies = await cursor.to_list(length=100)

            if all_replies:
                found = random.choice(all_replies)
                if found["reply_type"] == "text":
                    await message.reply_text(found["reply"])
                else:
                    await message.reply_sticker(found["reply"])

# --- ၃။ Delete Command ---
@Client.on_message(filters.command("del") & filters.group)
async def delete_reply(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return 

    if not message.reply_to_message:
        return await message.reply_text("❌ ဖျက်ချင်တဲ့စာကို Reply ပြန်ပြီး /del ရိုက်ပါ။")

    target = message.reply_to_message
    val_to_del = target.text.lower().strip() if target.text else (target.sticker.file_unique_id if target.sticker else None)
    
    res = await replies.delete_many({"$or": [{"trigger": val_to_del}, {"reply": val_to_del}]})

    if res.deleted_count > 0:
        await message.reply_text(f"🗑️ {res.deleted_count} ခု ဖျက်လိုက်ပါပြီ။")
    else:
        await message.reply_text("❌ ရှာမတွေ့ပါ။")
