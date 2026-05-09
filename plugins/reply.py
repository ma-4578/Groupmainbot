import os
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

# --- Database Setup (တိုက်ရိုက်ချိတ်ဆက်ခြင်း) ---
MONGO_URL = os.environ.get("MONGO_URL", "")
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Khh_db"]
replies = db["auto_replies"]

#  Variable ထဲက OWNER_ID ကို ယူမယ်
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

@Client.on_message(filters.command("del") & filters.group)
async def delete_reply(client: Client, message: Message):
    # Owner စစ်ဆေးခြင်း
    if message.from_user.id != OWNER_ID:
        return 

    if not message.reply_to_message:
        return await message.reply_text("❌ ဖျက်ချင်တဲ့စာ (အမေးစာ သို့မဟုတ် Bot ရဲ့အဖြေစာ) ကို Reply ပြန်ပြီး /del လို့ ရိုက်ပါ။")

    reply_to = message.reply_to_message
    
    # ၁။ Reply ထောက်ထားတဲ့စာက 'အမေးစာ (Trigger)' ဖြစ်နေရင် ဖျက်ဖို့ ID ယူမယ်
    trigger = None
    if reply_to.text:
        trigger = reply_to.text.lower().strip()
    elif reply_to.sticker:
        trigger = reply_to.sticker.file_unique_id

    # ၂။ Reply ထောက်ထားတဲ့စာက 'Bot ရဲ့ အဖြေစာ (Reply Content)' ဖြစ်နေရင် ဖျက်ဖို့ ID ယူမယ်
    reply_content = reply_to.text if reply_to.text else (reply_to.sticker.file_id if reply_to.sticker else None)

    # Database ထဲမှာ Trigger အနေနဲ့ ရှိနေရင် အရင်ဖျက်မယ်
    result = await replies.delete_many({"trigger": trigger})
    
    # တကယ်လို့ Trigger အနေနဲ့ ရှာမတွေ့ရင် (Bot ရဲ့ အဖြေကို reply ထောက်ထားတာဆိုရင်) အဖြေစာအနေနဲ့ ရှာဖျက်မယ်
    if result.deleted_count == 0 and reply_content:
        result = await replies.delete_many({"reply": reply_content})

    if result.deleted_count > 0:
        await message.reply_text(f"🗑️ သက်ဆိုင်ရာ အချက်အလက်များကို Data ထဲက ဖျက်လိုက်ပါပြီ။")
    else:
        await message.reply_text("❌ ဒီစာသားအတွက် မှတ်ထားတဲ့ အချက်အလက် ရှာမတွေ့ပါ။")

@Client.on_message(filters.group & ~filters.bot)
async def auto_learn_and_reply(client: Client, message: Message):
    # --- ၁။ Auto Learning (မရှိမှမှတ်မယ် - အရင်ပုံစံ) ---
    if message.reply_to_message:
        reply_to = message.reply_to_message
        trigger = reply_to.text.lower().strip() if reply_to.text else (reply_to.sticker.file_unique_id if reply_to.sticker else None)
        
        if trigger:
            reply_data = message.text if message.text else (message.sticker.file_id if message.sticker else None)
            reply_type = "text" if message.text else ("sticker" if message.sticker else None)

            if reply_data:
                # အမေးစာ ရှိမရှိ အရင်စစ်မယ်
                exists = await replies.find_one({"trigger": trigger})
                if not exists:
                    await replies.insert_one({
                        "trigger": trigger,
                        "reply": reply_data,
                        "reply_type": reply_type
                    })
    # --- ၂။ Auto Reply ---
    else:
        current_trigger = message.text.lower().strip() if message.text else (message.sticker.file_unique_id if message.sticker else None)
        if current_trigger:
            found = await replies.find_one({"trigger": current_trigger})
            if found:
                if found["reply_type"] == "text":
                    await message.reply_text(found["reply"])
                else:
                    await message.reply_sticker(found["reply"])
