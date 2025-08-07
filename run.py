import asyncio

from config import bot, dp
from app.aiogram import router
import app.telethone as telegram
from app.vk import VK

async def run():
    dp.include_router(router)

    tg_parser_task = telegram.init("@snowdr4am5")
    aiogram_task = dp.start_polling(bot)
    vkontakte_init = VK()

    await asyncio.gather(
        tg_parser_task,
        vkontakte_init.run(),
        aiogram_task
    )

if __name__ == "__main__":
    asyncio.run(run())