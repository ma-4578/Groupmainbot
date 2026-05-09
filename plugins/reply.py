import os
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

# --- Database ကို ဒီဖိုင်ထဲမှာတင် တိုက်ရိုက်ချိတ်မယ် (Circular Import ကင်းအောင်) ---
MONGO_URL = os.environ.get("MONGO_URL", "")
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Khh_db"] 
replies = db["auto_replies"]

OWNER_ID = int(os.environ.get("OWNER_ID", 0))

@Client.on_message(filters.group & ~filters.bot)
async def auto_learn_and_reply(client: Client, message: Message):
    # --- ၁။ စာသင်ယူခြင်း (Auto Learning) ---
    if message.reply_to_message:
        reply_to = message.reply_to_message
        trigger = None
        
        # Sticker ဆိုရင် ID နဲ့မှတ်မယ်၊ စာဆိုရင် စာသားနဲ့မှတ်မယ်
        if reply_to.text:
            trigger = reply_to.text.lower().strip()
        elif reply_to.sticker:
            trigger = reply_to.sticker.file_unique_id

        if trigger:
            # အဖြေစာကို စစ်မယ်
            reply_data = message.text if message.text else (message.sticker.file_id if message.sticker else None)
            reply_type = "text" if message.text else ("sticker" if message.sticker else None)

            if reply_data:
                # ရှိပြီးသားစာဆိုရင် ထပ်မမှတ်ဘူး (if not exists logic)
                exists = await replies.find_one({"trigger": trigger})
                if not exists:
                    await replies.insert_one({
                        "trigger": trigger,
                        "reply": reply_data,
                        "reply_type": reply_type
                    })

    # --- ၂။ အလိုအလျောက် ပြန်ဖြေခြင်း (Auto Reply) ---
    else:
        current_trigger = message.text.lower().strip() if message.text else (message.sticker.file_unique_id if message.sticker else None)
        
        if current_trigger:
            found = await replies.find_one({"trigger": current_trigger})
            if found:
                if found["reply_type"] == "text":
                    await message.reply_text(found["reply"])
                else:
                    await message.reply_sticker(found["reply"])

# --- ၃။ Delete Command ---
@Client.on_message(filters.command("del"))
async def delete_reply(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return 

    if not message.reply_to_message:
        return await message.reply_text("❌ ဖျက်ချင်တဲ့စာကို Reply ပြန်ပြီး /del ရိုက်ပါ။")

    reply_to = message.reply_to_message
    trigger_to_del = reply_to.text.lower().strip() if reply_to.text else (reply_to.sticker.file_unique_id if reply_to.sticker else None)

    if trigger_to_del:
        await replies.delete_one({"trigger": trigger_to_del})
        await message.reply_text(f"🗑️ '{trigger_to_del}' ကို ဖျက်လိုက်ပါပြီ။")
