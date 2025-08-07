import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher


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


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
