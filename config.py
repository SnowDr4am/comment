import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage


load_dotenv()

# Telethon
API_ID=os.getenv("API_ID")
API_HASH=os.getenv("API_HASH")

# VK
VK_TOKEN=os.getenv("VK_TOKEN")

# Aiogram
BOT_TOKEN=os.getenv("BOT_TOKEN")

# Other
BITRIX_LEAD_ADD_LC_API=os.getenv("BITRIX_LEAD_ADD_LC_API")
REDIS_PASSWORD=os.getenv("REDIS_PASSWORD")


redis_client = Redis(
    host='127.0.0.1',
    port=6379,
    password=REDIS_PASSWORD,
    db=15
)
storage = RedisStorage(redis=redis_client)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)