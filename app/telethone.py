from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.tl.functions.messages import GetHistoryRequest

from config import API_ID, API_HASH
from .utils import send_message_to_channel


client: TelegramClient | None = None
discussion_chat_id: int | None = None

async def init(channel_username: str):
    global client, discussion_chat_id
    client = TelegramClient(
            session="account",
            api_id=API_ID,
            api_hash=API_HASH,
            system_version="Windows 11",
            app_version="5.7.2 x64",
            lang_code="ru"
        )
    await client.start()

    channel = await client(GetFullChannelRequest(channel=channel_username))
    discussion_chat_id = channel.full_chat.linked_chat_id

    @client.on(events.NewMessage(chats=discussion_chat_id))
    async def handler(event):
        comment = event.message

        msg, sender_id = await generate_message_text(comment, discussion_chat_id)

        await send_message_to_channel({"log_text": msg, "telegram_user_id": sender_id})

    await client.run_until_disconnected()



async def generate_message_text(comment, discussion_chat_id):
    author = "Аноним"
    sender = await comment.get_sender()
    if sender:
        if sender.username:
            author = f"@{sender.username}"
        elif sender.first_name or sender.last_name:
            author = f"{sender.first_name or ''} {sender.last_name or ''}".strip()

    msg_id = comment.id
    reply_to_msg_id = None
    if comment.reply_to:
        reply_to_msg_id = comment.reply_to.reply_to_msg_id

    chat_id_str = str(discussion_chat_id)

    post_link = f"https://t.me/c/{chat_id_str}/{reply_to_msg_id}"
    comment_link = f"https://t.me/c/{chat_id_str}/{msg_id}"

    text = comment.text or "<без текста>"

    msg = (
        f"💬 <b>Новый комментарий TG</b>\n\n"
        f"👤 <b>От кого:</b>\n{author}\n\n"
        f"🔗 <b>Ссылка на пост:</b>\n<a href='{post_link}'>Перейти к посту</a>\n\n"
        f"🔗 <b>Ссылка на комментарий:</b>\n<a href='{comment_link}'>Перейти к комментарию</a>\n\n"
        f"📝 <b>Текст комментария:</b>\n{text}"
    )

    return msg, sender.id


async def ban_and_cleanup_user(user_telegram_id: int) -> bool:
    try:
        rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_polls=True,
            change_info=True,
            invite_users=True,
            pin_messages=True
        )

        await client(EditBannedRequest(
            channel=discussion_chat_id,
            participant=user_telegram_id,
            banned_rights=rights
        ))

        messages_to_delete = []
        history = await client(GetHistoryRequest(
            peer=discussion_chat_id,
            limit=200,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        for msg in history.messages:
            if msg.sender_id == user_telegram_id:
                messages_to_delete.append(msg.id)

        if messages_to_delete:
            await client.delete_messages(
                entity=discussion_chat_id,
                message_ids=messages_to_delete
            )

        return True

    except Exception as e:
        print(f"Ошибка при блокировке {user_telegram_id}: {e}")
        return False
