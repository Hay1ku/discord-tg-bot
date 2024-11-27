import os
import re
from aiogram import types, Router
from aiogram.filters import CommandStart, Command
import discord
from names import names, names_content

tg_user_router = Router()

@tg_user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Это была команда старт')

@tg_user_router.message(Command('sky1'))
async def sky_tg_user(message: types.Message):
    await message.answer('Введите город:')

# async def send_to_discord(content: str):
#     ds_chanel = bot.get_channel(1305873608018755649)
#     if ds_chanel:
#         await ds_chanel.send(content)

# @dp.message(Command('all'))
# async def all_tg_user(message: types.Message):
#     dog = re.findall(r'/[A-Za-z]+', message.text)
#     if f'@'+message.from_user.username in names_content.values():
#         target_value = f'@' + message.from_user.username
#         key = next((k for k, v in names_content.items() if v == target_value), None)
#         # mod = message.text
#         content = f'{key}:\n{message.text.replace(dog[0], '')}'
#     else:
#         content = f'{message.from_user.username}:\n{message.text.replace(dog[0], '')}'
#     await send_to_discord(content)  
#     # await message.reply("Сообщение отправлено в Discord.")