import discord
from discord import app_commands
from discord.ext import commands
import os

ds_channel = (int(os.getenv('DISCORD_CHANNEL_ID_BOT')))

class Commands_all(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @app_commands.command(name='join', description="Зайти в голосовой чат.")
    async def join(self, interaction: discord.Interaction):
        """Зайти в голосовой чат."""
        if interaction.channel.id == ds_channel:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
                await interaction.response.send_message(f'Подключился к каналу: {channel.name}')
            else:
                await interaction.response.send_message(f'Ты должен быть в голосовом канале.')

    @app_commands.command(name="leave", description="Выйти из голосового канала.")
    async def dis(self, interaction: discord.Interaction):
        """Выйти из голосового чата."""
        if interaction.channel.id == ds_channel:
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect() 
                await interaction.response.send_message('Отключился от голосового канала.')
            else:
                await interaction.response.send_message('Я не подключен к голосовому каналу.')

    @app_commands.command(name="help", description="Выводит список все команд")
    async def help(self, interaction: discord.Interaction):
        help_text = """
    **Музыкальные команды:**

    `/play <любой текст> или <ссылка> или <ссылка на плейлист>` - Играет трек или добавляет его в очередь.
    `/next` - Пропускает текущий трек.
    `/queue` - Показывает текущую очередь.
    `/pause` - Приостановка воспроизведение текущей песни.
    `/resume` - Возобновить воспроизведение приостановленной песни.
    `/stop` - Останавливает воспроизведение и очищает очередь.
    `/re <время в секундах>` - Перемотка на заданное количество секунд (перемотка не всегда работает)

    **Spotify команды:**
    `/recommendations` - Добавляет в очередь рекомендуемые треки.

    **Другие команды:**
    `/join` - Зайти в голосовой чат.
    `/leave` - Выйти из голосового чата.
    """
        await interaction.response.send_message(help_text)

async def setup(bot):
    await bot.add_cog(Commands_all(bot))