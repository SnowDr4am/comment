import aiohttp
from datetime import datetime, timezone, timedelta

from config import BITRIX_LEAD_ADD_LC_API


async def add_bitrix_lead(title: str = None, name: str = None, source_description: str = None, phone: str = None):
    fields = {}

    if title is not None:
        fields["TITLE"] = title
    if name is not None:
        fields["NAME"] = name
    if source_description is not None:
        fields["SOURCE_DESCRIPTION"] = source_description
    if phone is not None:
        fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "WORK"}]

    ekb_time = datetime.now(timezone.utc) + timedelta(hours=5)
    fields["UF_CRM_1495422921"] = ekb_time.strftime("%d.%m.%Y %H:%M:%S")

    payload = {
        "fields": fields,
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(BITRIX_LEAD_ADD_LC_API, json=payload) as response:
            result = await response.json()

            return result