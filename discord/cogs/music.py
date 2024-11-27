import discord
from discord.ext import commands
import urllib.parse, urllib.request, re, os
import asyncio
import yt_dlp
from spoty import get_daily_playlists

youtube_base_url = 'https://www.youtube.com/'
youtube_results_url = youtube_base_url + 'results?'
youtube_watch_url = youtube_base_url + 'watch?v='
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}
ds_channel = int(os.getenv('DISCORD_CHANNEL_ID_BOT'))

# Операции над очередью
class OperationsQueue:
    def __init__(self):
        self.yt_dl_options = {'format': 'bestaudio/best', 'ignoreerrors': True}
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dl_options)
    
    async def operationlinks(self, link):
        query_string = urllib.parse.urlencode({
            'search_query': link
        })

        content = urllib.request.urlopen(
            youtube_results_url + query_string
        )

        search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())
        # получаем ютуб ссылку на трек
        track = youtube_watch_url + search_results[0]
        return track
    
    async def get_info_track(self, track):
        loop = asyncio.get_event_loop() 
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(track, download=False))
        return data
    
    async def get_url_track(self, track):
        data = await self.get_info_track(track)
        song = data['url']
        return song
    
    async def get_title_track(self, track):
        if youtube_base_url in track:
            data = await self.get_info_track(track)
            video_title = data.get('title')
            duration = data.get('duration')
        else:
            video_title = track.get('title')
            duration = track.get('duration')
        title = {}
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            formatted_duration = f"{minutes}:{seconds}"
        else:
            formatted_duration = "Неизвестно"
        title[video_title] = formatted_duration    
        return title
    
    async def get_playlist_tracks(self, playlist_url):
        """Получение списка треков из YouTube плейлиста."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_flat': True,
            'ignoreerrors': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(playlist_url, download=False)
        if "entries" in data:
            return [youtube_watch_url + entry["id"] for entry in data["entries"]]
        return []
    
    async def clear_playlist_url(self, url):
        print(f'ГОвно')
        clean_url = re.sub(r'&list=.*', '', url)
        print(f'ГОвно2')
        return clean_url

# Основной интерфейс для работы с очередью
class MusicQueue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.voice_clients = {}
        self.lock = asyncio.Lock()
        self.is_playing = False
        self.current_track = None
        self.operationsqueue = OperationsQueue()

    async def add_to_queue(self, ctx, link):
        """Добавление трека в очередь."""
        async with self.lock:
            if ctx.guild.id not in self.queues:
                self.queues[ctx.guild.id] = []
            
            if youtube_base_url in link and "list=" not in link:
                self.queues[ctx.guild.id].append(link)

            if youtube_base_url not in link:
                link = await self.operationsqueue.operationlinks(link)
                self.queues[ctx.guild.id].append(link)
            
            if 'list=' in link and youtube_base_url in link and 'ab_channel=' not in link:
                link = await self.operationsqueue.get_playlist_tracks(link)
                self.queues[ctx.guild.id].extend(link)
            
            if 'list=' in link and youtube_base_url in link and 'ab_channel=' in link:
                print(f'моча')
                link = await self.operationsqueue.clear_playlist_url(link)
                self.queues[ctx.guild.id].append(link)
                print(f'моча')

            print(f"Трек добавлен: {link}")
        if not self.is_playing:
            await self.play_next(ctx.guild)

    async def play_next(self, guild):
        """Запуск следующего трека из очереди."""
        # async with self.lock:
        print(f"Очередь для {guild.id}: {self.queues.get(guild.id)}")
        if self.queues[guild.id] != [] and not self.is_playing:
            track = self.queues[guild.id].pop(0)
            self.is_playing = True

            print(f"Играет: {track}")
            await self._play_track(guild, track)

    async def _play_track(self, guild, track):
        """Запуск трека."""
        voice_client = self.voice_clients.get(guild.id) 
        if not voice_client or not voice_client.is_connected():
            self.voice_clients[guild.id] = voice_client

        data = await self.operationsqueue.get_info_track(track)
        song = data['url']
        await self.check_playing(data)
        self.current_track = song
        player = discord.FFmpegOpusAudio(executable=(str(os.getenv('PATH_TO_FFMPEG'))), source=song, **FFMPEG_OPTIONS)
        def after_play(e):
            self.bot.loop.create_task(self.on_track_end(guild))

        voice_client.play(player, after=after_play)
 

    async def on_track_end(self, guild):
        """Что делать после завершения трека."""
        async with self.lock:
            self.is_playing = False
            self.current_track = None
            await self.play_next(guild)

    async def skip_track(self, ctx):
        """Остановка трека."""
        if self.voice_clients[ctx.guild.id]:
            vc = self.voice_clients[ctx.guild.id]
            if vc.is_playing():
                vc.stop()
    
    # @tasks.loop(seconds=5)
    async def check_playing(self, data):
        """Что сейчас играет."""
        title = await self.operationsqueue.get_title_track(data)
        key, value = list(title.items())[0]
        embed = discord.Embed(title="", description=f'Сейчас играет: {key}\nПродолжительность {value}', color=discord.Color.green())
        channel = self.bot.get_channel(ds_channel)
        await channel.send(embed=embed)

# Проверка треков в очереди
class CheckQueue:
    def __init__(self, music_queue: MusicQueue):
        self.music_queue = music_queue
        self.operationsqueue = OperationsQueue()

    async def get_queue_partial(self, guild, limit=None):
        """Возвращает элементы очереди. Если указано limit, возвращает только limit элементов."""
        list_queues = self.music_queue.queues.get(guild.id)
        if not list_queues:
            return False

        data = list_queues[:limit] if limit else list_queues

        queue_dict = {}
        for tracks in data:
            result = await self.operationsqueue.get_title_track(tracks)
            queue_dict.update(result)
        return queue_dict

    async def get_low_queue(self, guild):
        """Возвращает первые 5 элементов очереди."""
        return await self.get_queue_partial(guild, limit=5)

    async def get_queue(self, guild):
        """Возвращает всю очередь."""
        return await self.get_queue_partial(guild)
    
    async def is_queue_empty(self, guild):
        """Проверка, пуста ли очередь."""
        return self.music_queue.queues[guild.id] == []


# Отдельная join функция для музыкального класса
class VoiceJoiner:
    def __init__(self, music_queue: MusicQueue):
        self.music_queue = music_queue

    async def join_voice(self, ctx):
        """Присоединение к голосовому каналу."""
        voice_client = self.music_queue.voice_clients.get(ctx.guild.id)
        
        if not voice_client or not voice_client.is_connected():
            voice_client = await ctx.author.voice.channel.connect()
            self.music_queue.voice_clients[ctx.guild.id] = voice_client


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = MusicQueue(bot)
        self.voice_joiner = VoiceJoiner(self.music_queue)
        self.checkqueue = CheckQueue(self.music_queue)

    @commands.command(name="play")
    async def play(self, ctx, *, link):
        """Команда для добавления трека в очередь."""
        if ctx.channel.id == ds_channel:
            await self.voice_joiner.join_voice(ctx)
            await self.music_queue.add_to_queue(ctx, link)
            await ctx.send(f"Добавлено в очередь")

    @commands.command(name="next")
    async def skip(self, ctx):
        """Команда для пропуска текущего трека."""
        if ctx.channel.id == ds_channel:
            if not self.music_queue.is_playing:
                await ctx.send("Сейчас ничего не играет.")
                return
            await self.music_queue.skip_track(ctx)
            # await ctx.send("Track skipped.")

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        """Команда для отображения текущей очереди."""
        if ctx.channel.id == ds_channel:
            queue = self.music_queue.queues.get(ctx.guild.id)
            if queue:
                if len(queue) > 5:
                    queue_low = await self.checkqueue.get_low_queue(ctx.guild)
                    embed = discord.Embed(
                        title="Список треков в очереди:",
                        color=discord.Color.blue()
                    )
                    for index, (key, value) in enumerate(queue_low.items(), start=1):
                        embed.add_field(name=f"", value=f"{index}) Трек - **{key}** Продолжительность - **{value}**", inline=False)
                    embed.add_field(name="", value=f"⬇️⬇️⬇️", inline=False)
                    embed.add_field(name="", value=f"**И ещё {int(len(queue)) - 5} композиций**", inline=False)
                    channel = self.bot.get_channel(ds_channel)
                    await channel.send(embed=embed)
                else:
                    queue = await self.checkqueue.get_queue(ctx.guild)
                    embed = discord.Embed(
                        title="Список треков в очереди:",
                        color=discord.Color.blue()
                    )
                    for index, (key, value) in enumerate(queue.items(), start=1):
                        embed.add_field(name=f"", value=f"{index}) Трек - **{key}** Продолжительность - **{value}**", inline=False)
                    channel = self.bot.get_channel(ds_channel)
                    await channel.send(embed=embed)
            else:
                await ctx.send("Очередь пуста")

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Команда для паузы текущего трека."""
        if ctx.channel.id == ds_channel:
            vc = self.music_queue.voice_clients[ctx.guild.id]
            if not vc or not vc.is_playing():
                embed = discord.Embed(title="", description="Сейчас ничего не воспроизводится.", color=discord.Color.green())
                return await ctx.send(embed=embed)
            elif vc.is_paused():
                return

            vc.pause()
            await ctx.send("Пауза ⏸️")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Команда для возобновления воспроизведения."""
        # Логика возобновления
        if ctx.channel.id == ds_channel:
            vc = self.music_queue.voice_clients[ctx.guild.id]

            if not vc or not vc.is_connected():
                embed = discord.Embed(title="", description="Нечего воспроизводить", color=discord.Color.green())
                return await ctx.send(embed=embed)
            elif not vc.is_paused():
                return

            vc.resume()
            await ctx.send("Возобновление ⏯️")

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Останавливает воспроизведение и очищает очередь."""
        if ctx.channel.id == ds_channel:
            vc = self.music_queue.voice_clients[ctx.guild.id]
            if vc.is_playing():
                self.music_queue.queues.clear()
                vc.stop()
                self.music_queue.is_playing = False
                self.music_queue.current_track = None
                await ctx.send(f'Стоп ⛔')
    

    # ДИСКОРД КОМАНДЫ СВЯЗАННЫЕ С SPOTIFY
    @commands.command(name='recommendations', description='Добавляет в очередь рекомендуемые треки')
    async def recommendations(self, ctx):
        if ctx.channel.id == ds_channel:
            await self.music_queue.join_voice(ctx)
            playlist_sp = get_daily_playlists()
            for list in playlist_sp:
                await self.music_queue.add_to_queue(ctx, list)
            embed = discord.Embed(title="", description="В очередь добавлен рекомендуемый плейлист spotify.", color=discord.Color.green())
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
    await bot.add_cog(MusicQueue(bot))
