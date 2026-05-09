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
    # --- ၁။ Auto Learning (အမေးတူလည်း အဖြေအသစ်ဆိုရင် ထပ်မှတ်မယ်) ---
    if message.reply_to_message:
        reply_to = message.reply_to_message
        
        # Bot အချင်းချင်း ပြန်ဖြေတာတွေကို လိုက်မမှတ်အောင် တားဆီးမယ်
        if reply_to.from_user and reply_to.from_user.is_bot:
            return

        trigger = None
        trigger_type = None
        
        if reply_to.text:
            trigger = reply_to.text.lower().strip()
            trigger_type = "text"
        elif reply_to.sticker:
            trigger = reply_to.sticker.file_unique_id
            trigger_type = "sticker"

        if trigger:
            reply_data = message.text if message.text else (message.sticker.file_id if message.sticker else None)
            reply_type = "text" if message.text else ("sticker" if message.sticker else None)

            if reply_data:
                # အမေးရော အဖြေရော အတိအကျတူနေမှသာ မမှတ်တော့မှာပါ
                exists = await replies.find_one({"trigger": trigger, "reply": reply_data})
                if not exists:
                    await replies.insert_one({
                        "trigger": trigger,
                        "trigger_type": trigger_type,
                        "reply": reply_data,
                        "reply_type": reply_type
                    })
                    # စာမှတ်မိသွားကြောင်း သိရအောင် ✅ Reaction ပြမယ်
                    try:
                        await message.add_reaction("✅")
                    except:
                        pass

    # --- ၂။ Auto Reply (အမေးတူတာတွေထဲက တစ်ခုကို Random ရွေးဖြေမယ်) ---
    else:
        current_trigger = None
        if message.text:
            current_trigger = message.text.lower().strip()
        elif message.sticker:
            current_trigger = message.sticker.file_unique_id

        if current_trigger:
            # အမေးနဲ့ကိုက်ညီတဲ့ အဖြေအားလုံးကို ရှာမယ်
            cursor = replies.find({"trigger": current_trigger})
            all_replies = await cursor.to_list(length=100)

            if all_replies:
                # ရှာတွေ့တဲ့အထဲက တစ်ခုကို Random ရွေးမယ်
                found = random.choice(all_replies)
                
                if found["reply_type"] == "text":
                    await message.reply_text(found["reply"])
                else:
                    await message.reply_sticker(found["reply"])

# --- ၃။ Delete Command (Reply ထောက်ထားတဲ့ အဖြေတစ်ခုချင်းစီကို ဖျက်မယ်) ---
@Client.on_message(filters.command("del") & filters.group)
async def delete_reply(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return 

    if not message.reply_to_message:
        return await message.reply_text("❌ ဖျက်ချင်တဲ့စာကို Reply ပြန်ပြီး /del ရိုက်ပါ။")

    target = message.reply_to_message
    
    # စာသား သို့မဟုတ် Sticker ID ကို ယူမယ်
    val_to_del = target.text.lower().strip() if target.text else (target.sticker.file_unique_id if target.sticker else None)
    reply_val = target.text if target.text else target.sticker.file_id

    # အမေးစာ (Trigger) အဖြစ်ရှိနေရင် အဲ့ဒီအမေးနဲ့ဆိုင်တဲ့ အဖြေအားလုံး ပျက်မယ်
    res1 = await replies.delete_many({"trigger": val_to_del})
    
    # အဖြေစာ (Reply) အဖြစ်ရှိနေရင် အဲ့ဒီအဖြေတစ်ခုပဲ ပျက်မယ်
    res2 = await replies.delete_many({"reply": reply_val})

    if res1.deleted_count > 0 or res2.deleted_count > 0:
        await message.reply_text("🗑️ ဖျက်သိမ်းပြီးပါပြီ။")
    else:
        await message.reply_text("❌ Database မှာ ရှာမတွေ့ပါ။")
