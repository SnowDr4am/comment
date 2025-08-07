from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import bot


CHANNEL_OUTPUT_ID = -1002881031125


async def send_message_to_channel(data: dict):
    log_text = data['log_text']
    telegram_user_id = data.get('telegram_user_id')

    keyboard = await comment_manager(telegram_user_id)

    sent_message = await bot.send_message(
        chat_id=CHANNEL_OUTPUT_ID,
        text=log_text,
        parse_mode='HTML'
    )

    keyboard = await comment_manager(sent_message.message_id, telegram_user_id)

    await bot.edit_message_reply_markup(
        chat_id=CHANNEL_OUTPUT_ID,
        message_id=sent_message.message_id,
        reply_markup=keyboard
    )


async def comment_manager(message_id: int, telegram_user_id: int = None) -> InlineKeyboardMarkup:
    bot_me = await bot.get_me()
    bot_username = bot_me.username

    create_lead_url = f"https://t.me/{bot_username}?start={message_id}"

    buttons = [
        [InlineKeyboardButton(text="📝 Сформировать лид", url=create_lead_url)]
    ]

    if telegram_user_id:
        buttons.append([
            InlineKeyboardButton(
                text="🚫 Заблокировать пользователя",
                callback_data=f"ban_user:{telegram_user_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🗑 Удалить сообщение", callback_data="delete_message")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)