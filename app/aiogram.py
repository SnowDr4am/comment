import re
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

import app.telethone as telegram
from .bitrix import add_bitrix_lead


router = Router()
CHANNEL_OUTPUT_ID = -1002881031125


@router.callback_query(F.data=="delete_message")
async def delete_message(callback: CallbackQuery):
    print(1)
    try:
        await callback.message.delete()
    except Exception:
        await callback.answer(f"Не удалось удалить сообщение\n\nСделайте это в ручную", show_alert=True)


@router.callback_query(F.data.startswith("ban_user:"))
async def ban_user(callback: CallbackQuery):
    message_id = callback.message.message_id
    telegram_user_id = int(callback.data.split(":")[1])

    result = await telegram.ban_and_cleanup_user(telegram_user_id)
    if result:
        await callback.answer("✅ Пользователь заблокирован")
        await callback.message.delete()
    else:
        await callback.answer("❌ Ошибка при блокировке", show_alert=True)


class CreateLeadStates(StatesGroup):
    waiting_title = State()
    waiting_phone = State()
    waiting_name = State()
    waiting_description = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.text:
        message_id = int(message.text.split(' ')[1]) if len(message.text.split(' ')) > 1 else None
    else:
        message_id = None

    if not message_id:
        await message.answer("Привет, друг")
        return
    else:
        try:
            await message.bot.delete_message(chat_id=CHANNEL_OUTPUT_ID, message_id=message_id)
        except Exception as e:
            await message.answer(f"❌ Ошибка удаления сообщения: {e}")
            print(f"[Удаление не удалось] {e}")

    try:
        member = await message.bot.get_chat_member(chat_id=CHANNEL_OUTPUT_ID, user_id=message.from_user.id)
        if member.status in ("member", "administrator", "creator"):
            await state.set_state(CreateLeadStates.waiting_title)
            await message.answer("Введите название для лида")
        else:
            await message.answer("❌ Вы должны быть участником нашей группы, чтобы создавать лиды")
    except TelegramBadRequest as e:
        await message.answer("❌ Ошибка проверки членства в группе. Убедитесь, что вы подписаны на группу")


@router.message(CreateLeadStates.waiting_title)
async def process_lead_title(message: Message, state: FSMContext):
    if message.chat.id != message.from_user.id:
        return

    text = message.text.strip()
    if not text:
        await message.answer("❌ Название лида не может быть пустым. Попробуйте еще раз.")
        return
    await state.update_data(lead_title=text)
    await message.answer("Введите номер телефона клиента (например, +79001234567)")
    await state.set_state(CreateLeadStates.waiting_phone)


@router.message(CreateLeadStates.waiting_phone)
async def process_lead_phone(message: Message, state: FSMContext):
    if message.chat.id != message.from_user.id:
        return

    raw_text = message.text.strip()

    digits = re.sub(r'\D', '', raw_text)

    if len(digits) != 11 or not digits.startswith(('7', '8')):
        await message.answer("❌ Номер должен состоять из 11 цифр и начинаться с 7 или 8. Пример: +79001234567")
        return

    normalized = '+7' + digits[1:]

    await state.update_data(phone=normalized)
    await message.answer("Введите имя клиента")
    await state.set_state(CreateLeadStates.waiting_name)


@router.message(CreateLeadStates.waiting_name)
async def process_client_name(message: Message, state: FSMContext):
    if message.chat.id != message.from_user.id:
        return

    text = message.text.strip()
    if not text:
        await message.answer("❌ Имя клиента не может быть пустым. Попробуйте еще раз.")
        return
    await state.update_data(client_name=text)
    await message.answer("Введите дополнительную информацию об источнике (или напишите '-' если нет)")
    await state.set_state(CreateLeadStates.waiting_description)


@router.message(CreateLeadStates.waiting_description)
async def process_lead_description(message: Message, state: FSMContext):
    if message.chat.id != message.from_user.id:
        return

    description = message.text.strip() or '-'

    data = await state.get_data()
    lead_title = data.get("lead_title")
    phone = data.get("phone")
    client_name = data.get("client_name")

    await add_bitrix_lead(title=lead_title, name=client_name, source_description=description, phone=phone)

    await message.answer(
        f"✅ Лид создан:\n"
        f"Название: {lead_title}\n"
        f"Телефон: {phone}\n"
        f"Имя клиента: {client_name}\n"
        f"Дополнительно: {description}"
    )

    await state.clear()