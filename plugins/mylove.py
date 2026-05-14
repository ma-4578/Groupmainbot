import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.command("mylove") & filters.group)
async def find_my_love(client: Client, message: Message):
    chat_id = message.chat.id
    user_mention = message.from_user.mention
    
    # ၁။ Group ထဲက Member စာရင်းကို ဆွဲထုတ်မယ်
    members = []
    async for member in client.get_chat_members(chat_id, limit=100):
        # Bot တွေနဲ့ ကိုယ့်ကိုယ်ကို ပြန်မရွေးအောင် စစ်မယ်
        if not member.user.is_bot and member.user.id != message.from_user.id:
            members.append(member.user)

    # ၂။ ရွေးစရာ Member မရှိရင် (ဥပမာ- Group ထဲမှာ ကိုယ်တစ်ယောက်တည်း ရှိနေရင်)
    if len(members) < 1:
        return await message.reply_text("⚠️  ဒီ Group ထဲမှာ သင်တစ်ယောက်တည်းပဲ ရှိနေလို့ ရှာမတွေ့နိုင်သေးပါဘူးဗျာ။")

    # ၃။ ကျပန်းတစ်ယောက်ကို ရွေးမယ်
    soulmate = random.choice(members)
    soulmate_mention = soulmate.mention

    # ၄။ ရလဒ်ကို စာသားအလှလေးနဲ့ ပြမယ်
    love_texts = [
        f"💖 {user_mention} ရေ... သင့်ရဲ့ ရှာဖွေနေသော ဖူးစာဖက်လေးကတော့ {soulmate_mention} ပဲ ဖြစ်ပါတယ်ခင်ဗျာ။",
        f"💘 ဝိုး... {user_mention} နဲ့ {soulmate_mention} ကတော့ တကယ့်ကို လိုက်ဖက်ညီတဲ့ စုံတွဲလေးပါပဲဗျာ။ ✨",
        f"🌹 {user_mention} ရဲ့ နှလုံးသားပိုင်ရှင်လေးကို ရှာတွေ့ပါပြီ! သူကတော့ {soulmate_mention} ပါတဲ့ဗျ။ 💍",
        f"🔥 ဖူးစာရှင်နတ်သားလေး ***HAN THAR*** က ဖန်တီးပေးလိုက်တဲ့ {user_mention} ရဲ့ တစ်သက်တာ အဖော်မွန်ကတော့ {soulmate_mention} ပါပဲ။ ❤️"
    ]
    
    # ၅။ ပိုပြီး ရင်ခုန်ဖို့အတွက် ခေတ္တစောင့်ခိုင်းမယ်
    msg = await message.reply_text("✨သင့် ဖူးစာရှင်ကို စစ်ဆေးနေပါသည်... ခေတ္တစောင့်ပါ။")
    await asyncio.sleep(2)
    
    # random ရွေးထားတဲ့ စာသားကို ပြောင်းလဲပေးမယ်
    await msg.edit(random.choice(love_texts))

