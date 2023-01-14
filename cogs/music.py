import discord 
import wavelink
import typing
import re
from discord.ext import commands
from discord import app_commands
from settings_bot import config

TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []
        self.position = 0
        self.repeat = False
        self.repeatMode = "NONE"
        self.playingTextChannel = 0
        bot.loop.create_task(self.create_node())

    async def create_node(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot, host="127.0.0.1", port="2333", password="youshallnotpass", region="europe")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node: <{node.identifier}> is now Ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: wavelink.player, track: wavelink.Track):
        try:
            self.queue.pup(0)
        except:
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        if str(reason) == "FINISHED":
            if not len(self.queue) == 0:
                next_track: wavelink.Track = self.queue[0]
                channel = self.bot.get_channel(self.playingTextChannel)

                try:
                    await player.play(next_track)
                except:
                    return await channel.send(embed=discord.Embed(
                        title=f"Now playing: {next_track.title}",
                        color=discord.Color.blurple()
                    ))
            else:
                pass
        else:
            print(reason)

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
            search = await wavelink.YouTubeTrack.search(query=query, return_first=True)
        except:
            return await interaction.response.send_message("", embed=discord.Embed(
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
            ))
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        member = interaction.guild.get_member(interaction.user.id)

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await member.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        if not vc.is_playing():
            try:
                await vc.play(search)
            except:
                return await interaction.response.send_message("", embed=discord.Embed(
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
            ))
        else:
            self.queue.append(search)

        embed_play = discord.Embed(title=f"Added {search} to the queue" , color=discord.Color.blurple())
        await interaction.response.send_message("", embed=embed_play)

    @app_commands.command(name="stop", description="Stop playing sound")
    async def stop_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)

        if player is None:
            return await interaction.response.send_message("Bot is not connected to any voice channel", ephemeral=True)

        self.queue.clear()
        
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
                player.play(track)
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
    
    @app_commands.command(name="playnow")
    async def play_now_command(self, interaction: discord.Integration, search: str):
        try:
            search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        except:
            return await interaction.response.send_message("", embed=discord.Embed(
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
            ))

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild)
        member = interaction.guild.get_member(interaction.user.id)

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await member.voice.channel(cls=wavelink.Player)
            await player.connect(member.voice.channel)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        try:
            await vc.play(search)
        except:
            return await interaction.response.send_message("", embed=discord.Embed(
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
            ))
        

        

async def setup(bot: commands.Bot):
    settings = config()
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=settings['main_guild']), discord.Object(id=617020672929169418)])