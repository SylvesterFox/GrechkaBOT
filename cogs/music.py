import discord 
import wavelink
import typing
import logging
import re
import asyncio
import datetime as dt
from discord.ext import commands
from discord import app_commands
from settings_bot import config

TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s(" \
            r")<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])) "


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger('LunaBot.cogs.Music')
        bot.loop.create_task(self.create_node())

    async def create_node(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot, host="127.0.0.1", port="2333", password="youshallnotpass",
                                            region="europe")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        self.log.info(f"Node: <{node.identifier}> is now Ready!")

    # @commands.Cog.listener()
    # async def on_wavelink_track_start(self, player: wavelink.player, track: wavelink.Track):
    #     try:
    #         self.queue.pup(0)
    #     except:
    #         pass

    # @commands.Cog.listener()
    # async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
    #     if str(reason) == "FINISHED":
    #         if not len(self.queue) == 0:
    #             next_track: wavelink.Track = self.queue[0]
    #             channel = self.bot.get_channel(self.playingTextChannel)

    #             try:
    #                 await player.play(next_track)
    #             except:
    #                 return await channel.send(embed=discord.Embed(
    #                     title=f"Now playing: {next_track.title}",
    #                     color=discord.Color.blurple()
    #                 ))
    #         else:
    #             pass
    #     else:
    #         print(reason, " test")

    @app_commands.command(name="join", description="Connection to the voice channel")
    async def join_voice(self, interaction: discord.Integration, channel: typing.Optional[discord.VoiceChannel] = None):
        if channel is None:
            try:
                member = interaction.guild.get_member(interaction.user.id)
                channel = member.voice.channel
            except AttributeError as e:
                return await interaction.response.send_message("Failed to connect...", ephemeral=True)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is not None:
            if player.is_connected():
                return await interaction.response.send_message("Bot is already connected to a voice channel", ephemeral=True)

        await channel.connect(cls=wavelink.Player)
        await interaction.response.send_message("Bot connect to the voice..", ephemeral=True)

    @app_commands.command(name="leave", description="Disconnect to the voice channel")
    async def leave_voice(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel", ephemeral=True)

        member = interaction.guild.get_member(interaction.user.id)
        member_bot = interaction.guild.get_member(self.bot.user.id)
        channel = member.voice

        if channel is None:
            return await interaction.response.send_message("You cannot use the command without being in the voice channel.", ephemeral=True)
        elif channel.channel.id != member_bot.voice.channel.id:
            return await interaction.response.send_message("You cannot use the command without being in the voice channel.", ephemeral=True)

        await player.disconnect()
        await interaction.response.send_message("Disconnected..", ephemeral=True)
        
    @app_commands.command(name="play", description="Staring play sound from URL")
    async def play_command(self, interaction: discord.Integration, query: str):
        try:
            search = await wavelink.YouTubeTrack.search(query=query)
        except Exception as e:
            print(e)
            return await interaction.response.send_message("", embed=discord.Embed(
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
            ))

        if search is None:
            return await interaction.response.send_message("No tracks found")

        mbed = discord.Embed(
            title="Select the track: ",
            description=("\n".join(f"**{i+1}. {t.title}**" for i, t in enumerate(search[:5]))),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message("", embed=mbed)
        msg = await interaction.original_response()
        channel = self.bot.get_channel(msg.channel.id)
        
        emojis_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '❌']
        emojis_dict = {
            '1️⃣': 0,
            "2️⃣": 1,
            "3️⃣": 2,
            "4️⃣": 3,
            "5️⃣": 4,
            "❌": -1
        }

        for emoji in list(emojis_list[:min(len(search), len(emojis_list))]):
            await msg.add_reaction(emoji)

        def check(res, user):
            return res.emoji in emojis_list and user == interaction.user and res.message.id == msg.id

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await msg.delete()
            return
        else:
            await msg.delete()

        member = interaction.guild.get_member(interaction.user.id)

        try:
            if emojis_dict[reaction.emoji] == -1: return
            choosed_track = search[emojis_dict[reaction.emoji]]
        except Exception as e:
            return print(e)

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await member.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        try:
            await vc.play(choosed_track)
        except Exception as e:
            print(e)
            return await channel.send("", embed=discord.Embed(
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
        ))

        embed_play = discord.Embed(title=f"Playing now {choosed_track}" , color=discord.Color.blurple())
        await channel.send("", embed=embed_play)

    @app_commands.command(name="stop", description="Stop playing sound")
    async def stop_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel", ephemeral=True)

        if player.is_playing:
            await player.stop()
            embed = discord.Embed(title="Playback Stoped", color=discord.Colour.blurple())
            await interaction.response.send_message("", embed=embed)
        else:
            return await interaction.response.send_message("Nothing Is playing right now", ephemeral=True)

    @app_commands.command(name="pause", description="Paused playback")
    async def pause_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel", ephemeral=True)

        if not player.is_paused():
            if player.is_playing():
                await player.pause()
                embed = discord.Embed(title="Playback Paused", color=discord.Color.blurple())
                await interaction.response.send_message("", embed=embed)
            else:
                return await interaction.response.send_message("Nothing Is playing right now", ephemeral=True)
        else:
            return await interaction.response.send_message("Playback is Aiready paused")

    @app_commands.command(name="resume", description="Playback resumed")
    async def resume_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel", ephemeral=True)
        
        if player.is_paused():
            await player.resume()
            embed = discord.Embed(title="Playback resumed", color=discord.Color.blurple())
            return await interaction.response.send_message("", embed=embed)
        else:
            if not len(self.queue) == 0:
                track: wavelink.track = self.queue[0]
                await player.play(track)
                return await interaction.response.send_message("", embed=discord.Embed(
                    title=f"Now playing: {track.title}",
                    color=discord.Color.blurple()
                ))
            else:
                return await interaction.response.send_message("Playblack is not paused")

    @app_commands.command(name="volume", description="Playback volume")
    async def volume_command(self, interaction: discord.Integration, to: int):
        if to > 100:
            return await interaction.response.send_message("Volume should between 0 and 100")
        elif to < 1:
            return await interaction.response.send_message("Volume should between 0 and 100")

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        await player.set_volume(to)
        embed = discord.Embed(title=f"Changed Volume to {to}", color=discord.Color.blurple())
        await interaction.response.send_message("", embed=embed)

    @app_commands.command(name="seek", description="Seek to the given position in the song.")
    async def seek_command(self, interaction: discord.Integration, seek: str):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)
        
        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel", ephemeral=True)

        if not (match := re.match(TIME_REGEX, seek)):
            return await interaction.response.send_message("Time code invalid", ephemeral=True)

        if match.group(3):
            secs = (int(match.group(1)) * 60) + (int(match.group(3)))
        else:
            secs = int(match.group(1))

        await player.seek(secs * 1000)
        await interaction.response.send_message("Seeked", ephemeral=True)

    @app_commands.command(name="nowplaying", description="Now playing sound")
    async def now_play_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel")
        
        if player.is_playing():
            mbed = discord.Embed(
                title="Now playing",
                color=discord.Colour.blurple(),
                timestamp=dt.datetime.utcnow()
            )
            mbed.set_author(name="Playback Infomation")
            mbed.add_field(name="Track title", value=player.track.info['title'], inline=False)
            mbed.add_field(name="Artist", value=player.track.info['author'], inline=False)
            t_sec = int(player.track.length)
            hour = int(t_sec/3600)
            min = int((t_sec % 3600) / 60)
            sec = int((t_sec % 3600) % 60)
            length = f"{hour}:{min}:{sec}" if not hour == 0 else f"{min}:{sec}"
            mbed.add_field(name="Length", value=f"{length}", inline=False)

            return await interaction.response.send_message(embed=mbed)
        else:
            return await interaction.response.send_message("Nothing is playing right now", ephemeral=True)


async def setup(bot: commands.Bot):
    settings = config()
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=settings['main_guild'])])
