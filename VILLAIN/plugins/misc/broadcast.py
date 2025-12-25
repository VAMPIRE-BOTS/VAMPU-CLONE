import asyncio

from pyrogram import filters, Client
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait

from VILLAIN import app
from VILLAIN.misc import SUDOERS
from VILLAIN.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)

# --- NEW IMPORTS FOR GLOBAL BROADCAST (VILLAIN) ---
# Ensure ki VILLAIN/utils/database/clonedb.py exist karta hai
from VILLAIN.utils.database.clonedb import get_served_chats_clone
from VILLAIN.core.mongo import pymongodb
from config import API_ID, API_HASH
# --------------------------------------------------

from VILLAIN.utils.decorators.language import language
from VILLAIN.utils.formatters import alpha_to_int
from config import adminlist

# Clone Database Define
clonebotdb = pymongodb.clonebotdb

IS_BROADCASTING = False


@app.on_message(filters.command("broadcast") & SUDOERS)
@language
async def braodcast_message(client, message, _):
    global IS_BROADCASTING
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        query = message.text.split(None, 1)[1]
        
        # Flags cleanup
        if "-pin" in query:
            query = query.replace("-pin", "")
        if "-nobot" in query:
            query = query.replace("-nobot", "")
        if "-pinloud" in query:
            query = query.replace("-pinloud", "")
        if "-assistant" in query:
            query = query.replace("-assistant", "")
        if "-user" in query:
            query = query.replace("-user", "")
        if "-all" in query:
            query = query.replace("-all", "")
            
        if query == "":
            return await message.reply_text(_["broad_8"])

    IS_BROADCASTING = True
    
    # ---------------------------------------------------------
    # GLOBAL BROADCAST LOGIC (-all) FOR VILLAIN REPO
    # ---------------------------------------------------------
    if "-all" in message.text:
        status_msg = await message.reply_text("🔄 **Global Broadcast Started on ALL CLONES...**\nIsme thoda waqt lag sakta hai.")
        
        # Database se saare clones fetch karo
        all_clones = clonebotdb.find({})
        total_clones_sent = 0
        
        for clone in all_clones:
            try:
                clone_token = clone.get("token")
                if not clone_token:
                    continue
                
                # Temp Client start karte hain clone ke liye
                temp_client = Client(
                    f"broadcast_{clone['bot_id']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=clone_token,
                    in_memory=True
                )
                await temp_client.start()
                
                # Clone ke chats nikalte hain (Imported from clonedb)
                clone_served_chats = await get_served_chats_clone(temp_client.me.id)
                
                for chat in clone_served_chats:
                    try:
                        chat_id = int(chat["chat_id"])
                        if message.reply_to_message:
                            await temp_client.forward_messages(chat_id, y, x)
                        else:
                            await temp_client.send_message(chat_id, text=query)
                        await asyncio.sleep(0.2)
                    except Exception:
                        pass
                
                await temp_client.stop()
                total_clones_sent += 1
            except Exception as e:
                # Agar kisi clone ka token expire hai ya error hai to skip karo
                pass
        
        await status_msg.edit_text(f"✅ **Global Broadcast Completed!**\nTotal Clones Processed: {total_clones_sent}")
        
        # Code niche continue karega taaki Main Bot (VILLAIN) ke chats me bhi broadcast ho

    await message.reply_text(_["broad_1"])

    # ---------------------------------------------------------
    # NORMAL MAIN BOT BROADCAST (EXISTING LOGIC)
    # ---------------------------------------------------------
    if "-nobot" not in message.text:
        sent = 0
        pin = 0
        chats = []
        schats = await get_served_chats()
        for chat in schats:
            chats.append(int(chat["chat_id"]))
        for i in chats:
            try:
                m = (
                    await app.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await app.send_message(i, text=query)
                )
                if "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except:
                        continue
                elif "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except:
                        continue
                sent += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                continue
        try:
            await message.reply_text(_["broad_3"].format(sent, pin))
        except:
            pass

    if "-user" in message.text:
        susr = 0
        served_users = []
        susers = await get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                m = (
                    await app.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await app.send_message(i, text=query)
                )
                susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                pass
        try:
            await message.reply_text(_["broad_4"].format(susr))
        except:
            pass

    if "-assistant" in message.text:
        aw = await message.reply_text(_["broad_5"])
        text = _["broad_6"]
        from VILLAIN.core.userbot import assistants

        for num in assistants:
            sent = 0
            client = await get_client(num)
            async for dialog in client.get_dialogs():
                try:
                    await client.forward_messages(
                        dialog.chat.id, y, x
                    ) if message.reply_to_message else await client.send_message(
                        dialog.chat.id, text=query
                    )
                    sent += 1
                    await asyncio.sleep(3)
                except FloodWait as fw:
                    flood_time = int(fw.value)
                    if flood_time > 200:
                        continue
                    await asyncio.sleep(flood_time)
                except:
                    continue
            text += _["broad_7"].format(num, sent)
        try:
            await aw.edit_text(text)
        except:
            pass
    IS_BROADCASTING = False


async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except:
            continue


asyncio.create_task(auto_clean())
