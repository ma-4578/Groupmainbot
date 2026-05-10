import asyncio
import re
import time
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions

# --- သတ်မှတ်ချက်များ ---
# သင့်ရဲ့ User ID ကို ဒီမှာ အမှန်အတိုင်း ပြောင်းထည့်ပါ
OWNER_ID = 8266394986

# Link စစ်တဲ့ ပုံစံ
LINK_PATTERN = r"(https?://\S+|t\.me/\S+|@\S+)"

# သတိပေးချက် မှတ်ရန်
warns = {}

@Client.on_message(filters.group & (filters.text | filters.forwarded))
async def auto_mute_handler(client: Client, message: Message):
    # ၁။ User မဟုတ်တဲ့ message (ဥပမာ- Channel post) ဖြစ်ရင် ကျော်မယ်
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # ၂။ Bot Owner ဖြစ်နေရင် ကျော်မယ် (မဖျက်ဘူး)
    if user_id == OWNER_ID:
        return

    # ၃။ Group Admin သို့မဟုတ် Group ပိုင်ရှင် ဖြစ်နေရင် ကျော်မယ် (မဖျက်ဘူး)
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return
    except Exception as e:
        # User ID ရှာမရတဲ့ error မျိုးဆိုရင်လည်း ရှေ့မဆက်တော့အောင် return လုပ်ထားတယ်
        print(f"Admin Check Error: {e}")
        return

    # --- ဒီအောက်က အပိုင်းဟာ Admin မဟုတ်တဲ့ သာမန် User တွေအတွက်ပဲ ဖြစ်ပါတယ် ---

    # Link ပါမပါ စစ်ဆေးခြင်း
    has_link = re.search(LINK_PATTERN, message.text) if message.text else False
    is_forwarded = bool(message.forward_date)

    if has_link or is_forwarded:
        user_key = f"{chat_id}:{user_id}"
        
        # သတိပေးချက် အကြိမ်ရေ တိုးမယ်
        current_warns = warns.get(user_key, 0) + 1
        warns[user_key] = current_warns

        if current_warns < 3:
            # --- သတိပေးစာ ပို့မယ် ---
            warn_msg = await message.reply_text(
                f"⚠️ {message.from_user.mention}၊  Link များ သို့မဟုတ် Forward များ ပို့ခွင့်မရှိပါ။\n"
                f"သတိပေးချက်: ({current_warns}/3)\n"
                f"၃ ကြိမ်ပြည့်ပါက ၁ မိနစ် Mute ခံရပါမည်။"
            )
            # Link ပါတဲ့ စာကို ဖျက်မယ်
            try:
                await message.delete()
            except:
                pass
            
            # သတိပေးစာကို ၁၀ စက္ကန့်အကြာမှာ ပြန်ဖျက်မယ်
            await asyncio.sleep(15)
            await warn_msg.delete()

        else:
            # --- ၃ ကြိမ်ပြည့်သွားရင် Mute မယ် ---
            try:
                # လက်ရှိအချိန် + ၆၀ စက္ကန့် (၁ မိနစ်)
                until_time = int(time.time() + 60)
                
                await message.chat.restrict_member(
                    user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_time
                )
                
                mute_msg = await message.reply_text(
                    f"🚫 {message.from_user.mention} သည် စည်းကမ်းဖောက်ဖျက်မှု ၃ ကြိမ်ပြည့်သဖြင့် ၁ မိနစ်ခန့် Mute ခံလိုက်ရသည်။"
                )
                
                # Warn counter ကို Reset ပြန်လုပ်မယ်
                warns[user_key] = 0
                
                # မူရင်းစာကို ဖျက်မယ်
                try:
                    await message.delete()
                except:
                    pass

                # Mute စာကို ၁ မိနစ်နေရင် ဖျက်မယ်
                await asyncio.sleep(60)
                await mute_msg.delete()

            except Exception as e:
                print(f"Mute Error: {e}")
