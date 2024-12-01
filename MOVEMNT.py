import asyncio
import random
import json
from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector

wallet_address = your_wallet
aid = []
taskid = []
async def capcha_get():
    async with ClientSession() as session:
        url = 'https://api.capmonster.cloud/createTask'
        json_payload = {
            "clientKey": "9dd87c3b9d80af56954124a6d8f982fb",  # Ваш ключ API CapMonster
            "task": {
                "type": "TurnstileTask",
                "websiteURL": "https://faucet.movementnetwork.xyz/?network=mevm",
                "websiteKey": "0x4AAAAAAAya3vu3EyR3DGUk",  # Замените на реальный SITE_KEY
                "userAgent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random.uniform(520, 540):.2f} (KHTML, like Gecko) Chrome/131.0.0.0 Safari/{random.uniform(520, 540):.2f}"
            }
        }

        async with session.post(url=url, json=json_payload) as response:
            data = await response.text() # response.json()
            aid.append(data)
    json_string = aid[0]
    parsed_data = json.loads(json_string)
    task_id = parsed_data.get("taskId")
   # print(task_id)
    taskid.append(str(task_id))
    if task_id > 0:
        print("Капча решена")
    else:print("Ошбика капчи(")



async def get_token():
    await capcha_get()
    async with ClientSession() as session:
        url = 'https://faucet.movementnetwork.xyz/api/rate-limit'
        data = {
            "adress": f"{wallet_address}",
            "config": {
                "mevm": {"network:" "devnet", "url:" "https://mevm.devnet.imola.movementlabs.xyz", "language:" "evm"}
            },
            "network": "mevm",
            "token": taskid[0]  # Токен капчи
        }
        payload = {"wallet": wallet_address}  # Тело запроса

        async with session.post(url=url, data=data) as response:
            data = await response.text()  # response.json()
            print(data)
            if response.status > 200:
                print()
                print("Server error")
            else:print("Саксесфул, чекай токены")



asyncio.run(get_token())
