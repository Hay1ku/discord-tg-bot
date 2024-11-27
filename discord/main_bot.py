import re
import logging
from dotenv import load_dotenv, find_dotenv
import os
from names import names, names_content
from io import BytesIO

# import spotipy
# from spotipy.oauth2 import SpotifyOAuth

import discord
from discord.ext import commands
# from discord import app_commands
# from discord import FFmpegOpusAudio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

import asyncio
import yt_dlp
import urllib.parse, urllib.request, re

load_dotenv(find_dotenv())
from routers_tg.tg_user import tg_user_router
logging.basicConfig(filename='discord/bot.log', level=logging.INFO)



# НАСТРОЙКИ ТЕЛЕГРАММ БОТА
ALLOWED_UPDATES = ['message', 'edited_message']
bot_tg = Bot(token=os.getenv('TOKEN_TELEGRAM')) 
dp = Dispatcher()
dp.include_routers(tg_user_router)


# НАСТРОЙКИ ДИСКОРД БОТА
intents = discord.Intents.default()
intents.messages = True 
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='/', intents=intents)

# БОТ ДИСКОРДА
@bot.event
async def on_ready():
    await bot.wait_until_ready() 
    print(f'Бот {bot.user} подключен к Discord!')
    
    cogs_path = os.path.join(os.path.dirname(__file__), 'cogs')
    for cog in os.listdir(cogs_path):
        if cog == '__init__.py':
            continue
        if cog.endswith('.py'):
            await bot.load_extension(f'cogs.{cog[:-3]}')
    
    try:
        await bot.tree.sync()
        print("Слэш-команды синхронизированы")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")


@bot.event
async def on_message(message):
    ds_chanel = bot.get_channel(int(os.getenv('DISCORD_CHANNEL_ID')))
    if message.channel.id == ds_chanel.id:
        if message.author == bot.user:
            return
        author_name = message.author.name
        
        if author_name in names:
            author_name = author_name.replace(author_name, names[author_name])

        mentions = re.findall(r'<@(\d+)>', message.content)
        modified_content = message.content
        
        for user_id in mentions:
            user_id = int(user_id)
            user = bot.get_user(user_id)
            if user is None:
                user = await bot.fetch_user(user_id)
            
            if user.name in names_content:
                modified_content = modified_content.replace(f'<@{user_id}>', names_content[user.name])
            else:
                modified_content = modified_content.replace(f'<@{user_id}>', f'{user.name}')

        urls = re.findall(r'https?://[^\s]+', modified_content)
        for url in urls:
            modified_content = modified_content.replace(url, f"[⬇️⬇️⬇️]({url})")

        if message.attachments:
            attachment = message.attachments[0]
            image_url = attachment.url
            text_content = f'{author_name}:\n{modified_content}\n[⬇️⬇️⬇️]({image_url})'
        else:
            text_content = f'{author_name}:\n{modified_content}'

        await bot_tg.send_message(chat_id=os.getenv('TELEGRAM_CHAT_ID'), text = text_content, parse_mode='Markdown')
    await bot.process_commands(message)


# БОТ ТЕЛЕГРАММА
async def send_to_discord(content: str,file: discord.File = None):
    ds_chanel = bot.get_channel(int(os.getenv('DISCORD_CHANNEL_ID')))
    if ds_chanel:
        if file:
            await ds_chanel.send(content, file=file)
        else:
            await ds_chanel.send(content)


@dp.message(Command('all'))
async def all_tg_user(message: types.Message):
    if message.text:
        dog = re.findall(r'/[A-Za-z]+', message.text)
        if f'@'+message.from_user.username in names_content.values():
            target_value = f'@' + message.from_user.username
            key = next((k for k, v in names_content.items() if v == target_value), None)
            content = f'{key}:\n{message.text.replace(dog[0], '')}'
        else:
            content = f'{message.from_user.username}:\n{message.text.replace(dog[0], '')}'
        
        await send_to_discord(content)
    
    else:
        file_id = message.document.file_id
        file = await bot_tg.get_file(file_id)
        file_path = file.file_path
        photo = await bot_tg.download_file(file_path)
        discord_file = discord.File(photo, filename="image.jpg")
        # file_url = f'https://api.telegram.org/file/bot{os.getenv("TOKEN_TELEGRAM")}/{file.file_path}'
        if f'@'+message.from_user.username in names_content.values():
            target_value = f'@' + message.from_user.username
            key = next((k for k, v in names_content.items() if v == target_value), None)
            content = f'{key}:\n'
        else:
            content = f'{message.from_user.username}:\n'
        await send_to_discord(content, file = discord_file)

async def main():
    tg_polling = asyncio.create_task(dp.start_polling(bot_tg, allowed_updates=ALLOWED_UPDATES))
    discord_polling = asyncio.create_task(bot.start(os.getenv('TOKEN_DISCORD')))
    delete_web = asyncio.create_task(bot_tg.delete_webhook(drop_pending_updates=True))

    await asyncio.gather(delete_web, tg_polling, discord_polling)



if __name__ == "__main__":
    asyncio.run(main())