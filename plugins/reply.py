import os
import random
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

# --- Database Setup ---
MONGO_URL = os.environ.get("MONGO_URL", "")
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Khh_db"]
replies = db["auto_replies_v2"]

OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# ======================
# HELPER FUNCTIONS
# ======================
def is_clean_text(text):
    if not text: return False
    # စာလုံးရေ ၁ လုံးအောက် သို့မဟုတ် ၁၅၀ ထက်များရင် မမှတ်ဘူး
    if len(text) < 1 or len(text) > 150: 
        return False
    # Link တွေ၊ @ ပါရင် မမှတ်ဘူး (Spam ကာကွယ်ရန်)
    if re.search(r'http[s]?://', text) or '@' in text: 
        return False
    return True

@Client.on_message(filters.group & ~filters.bot)
async def auto_learn_and_reply(client: Client, message: Message):
    
    # ၁။ စာသင်ယူခြင်း (Reply ထောက်ထားလျှင်)
    if message.reply_to_message:
        reply_to = message.reply_to_message
        
        # Bot အချင်းချင်း စာတွေကို မမှတ်ဘူး
        if reply_to.from_user and reply_to.from_user.is_bot:
            return

        trigger = None
        # အမေးစာသား (Trigger) ကို စစ်ဆေးယူမယ်
        if reply_to.text and is_clean_text(reply_to.text):
            trigger = reply_to.text.lower().strip()
        elif reply_to.sticker:
            trigger = reply_to.sticker.file_unique_id

        reply_data = None
        reply_type = None
        # အဖြေစာသား (Reply) ကို စစ်ဆေးယူမယ်
        if message.text and is_clean_text(message.text):
            reply_data = message.text
            reply_type = "text"
        elif message.sticker:
            reply_data = message.sticker.file_id
            reply_type = "sticker"

        if trigger and reply_data:
            # Database ထဲမှာ အဖြေတူတာ ရှိမရှိ အရင်စစ်မယ်
            exists = await replies.find_one({
                "trigger": trigger, 
                "reply": reply_data
            })
            
            if not exists:
                await replies.insert_one({
                    "trigger": trigger,
                    "reply": reply_data,
                    "reply_type": reply_type
                })
                # မှတ်မိကြောင်း 👍 ပြမယ်
                try:
                    await client.send_reaction(
                        chat_id=message.chat.id,
                        message_id=message.id,
                        emoji="👍"
                    )
                except:
                    pass

    # ၂။ အလိုအလျောက် ပြန်ဖြေခြင်း
    current_trigger = None
    if message.text:
        current_trigger = message.text.lower().strip()
    elif message.sticker:
        current_trigger = message.sticker.file_unique_id

    if current_trigger:
        # အမေးနဲ့ ကိုက်ညီတဲ့ အဖြေအားလုံးကို ရှာမယ်
        cursor = replies.find({"trigger": current_trigger})
        all_replies = await cursor.to_list(length=50)

        if all_replies:
            # အဖြေမျိုးစုံရှိရင် Random တစ်ခု ရွေးမယ်
            found = random.choice(all_replies)
            if found["reply_type"] == "text":
                await message.reply_text(found["reply"])
            else:
                await message.reply_sticker(found["reply"])

# ======================
# DELETE COMMAND
# ======================
@Client.on_message(filters.command("del") & filters.group)
async def delete_reply(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return 

    if not message.reply_to_message:
        return await message.reply_text("❌ ဖျက်ချင်တဲ့စာကို Reply ပြန်ပြီး /del ရိုက်ပါ။")

    target = message.reply_to_message
    val_to_del = None
    
    if target.text:
        val_to_del = target.text.lower().strip()
    elif target.sticker:
        val_to_del = target.sticker.file_unique_id

    if val_to_del:
        res = await replies.delete_many({"$or": [{"trigger": val_to_del}, {"reply": val_to_del}]})
        await message.reply_text(f"🗑️ {res.deleted_count} ခု ဖျက်လိုက်ပါပြီ။")
