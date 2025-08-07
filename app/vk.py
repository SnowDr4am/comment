import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta

from .utils import send_message_to_channel
from config import redis_client, VK_TOKEN


class VK:
    def __init__(self):
        self.token = VK_TOKEN
        self.group_id = 33153031
        self.api_url = "https://api.vk.com/method"
        self.vk_version = "5.131"
        self.session = aiohttp.ClientSession()

    async def fetch_user_info(self, from_id):
        try:
            if from_id > 0:
                params = {
                    "user_ids": str(from_id),
                    "access_token": self.token,
                    "v": self.vk_version,
                }
                async with self.session.get(f"{self.api_url}/users.get", params=params) as resp:
                    data = await resp.json()
                    if "response" in data and len(data["response"]) > 0:
                        user = data["response"][0]
                        first_name = user.get("first_name", "")
                        last_name = user.get("last_name", "")
                        full_name = f"{first_name} {last_name}".strip()
                        link = f"https://vk.com/id{from_id}"
                        return full_name, link
            else:
                group_id = abs(from_id)
                params = {
                    "group_id": str(group_id),
                    "access_token": self.token,
                    "v": self.vk_version,
                }
                async with self.session.get(f"{self.api_url}/groups.getById", params=params) as resp:
                    data = await resp.json()
                    if "response" in data and len(data["response"]) > 0:
                        group = data["response"][0]
                        name = group.get("name", "")
                        screen_name = group.get("screen_name", "")
                        link = f"https://vk.com/{screen_name}" if screen_name else ""
                        return name, link
        except Exception as e:
            print(f"⚠️ Ошибка при получении инфо пользователя/группы: {e}")
        return "Неизвестный пользователь", ""

    async def fetch_posts(self):
        params = {
            "access_token": self.token,
            "v": self.vk_version,
            "owner_id": -int(self.group_id),
            "count": 5
        }
        try:
            async with self.session.get(f"{self.api_url}/wall.get", params=params) as resp:
                return await resp.json()
        except Exception as e:
            print(f"⚠️ Ошибка при fetch_posts: {e}")
            return {}

    async def fetch_comments_for_post(self, post_id):
        params = {
            "access_token": self.token,
            "v": self.vk_version,
            "owner_id": -int(self.group_id),
            "post_id": post_id,
            "count": 100,
            "need_likes": 0,
            "extended": 0
        }
        try:
            async with self.session.get(f"{self.api_url}/wall.getComments", params=params) as resp:
                return await resp.json()
        except Exception as e:
            print(f"⚠️ Ошибка при fetch_comments_for_post: {e}")
            return {}

    async def run(self):
        try:
            print("✅ VKParser запущен и слушает обсуждения...")
            while True:
                posts_data = await self.fetch_posts()
                now = datetime.now(timezone.utc)
                if "response" in posts_data:
                    posts = posts_data["response"].get("items", [])
                    for post in posts:
                        post_id = post["id"]
                        comments_data = await self.fetch_comments_for_post(post_id)
                        if "response" in comments_data:
                            comments = comments_data["response"].get("items", [])
                            for item in comments:
                                comment_id = item["id"]
                                key = f"vk_comment:{comment_id}"
                                if await redis_client.exists(key):
                                    continue
                                date_unix = item.get("date")
                                if date_unix is None:
                                    continue
                                comment_date = datetime.fromtimestamp(date_unix, tz=timezone.utc)
                                comment_age = now - comment_date
                                if comment_age > timedelta(hours=24):
                                    continue
                                await redis_client.set(key, 1)
                                await redis_client.expire(key, 604800)

                                from_id = item.get("from_id")
                                text = item.get("text", "")

                                full_name, profile_link = await self.fetch_user_info(from_id)

                                if profile_link:
                                    author_display = f'<a href="{profile_link}">{full_name}</a>'
                                else:
                                    author_display = full_name

                                link = f"https://vk.com/wall-{self.group_id}_{post_id}?reply={comment_id}"

                                msg = (
                                    f"💬 Новый комментарий VK\n"
                                    f"👤 От кого пришло: {author_display}\n"
                                    f"🔗 Ссылка на комментарий: {link}\n"
                                    f"📝 Текст комментария: {text}"
                                )
                                await send_message_to_channel({"log_text": msg})
                await asyncio.sleep(60)
        finally:
            await self.session.close()