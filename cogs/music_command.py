import discord
import wavelink
import typing
import logging
import re
import asyncio

from discord.ext import commands
from discord import app_commands
from core.custom import LangMessageable
from cogs.music import CustomPlayer
from core.settings_bot import config
from core.database import GuildSettings

TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"


class MusicCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = GuildSettings()
        self.log = logging.getLogger(f'LunaBOT.{__name__}')
        self.send = LangMessageable.mod_send
        self.send_embed = LangMessageable.send_embed
        self.send_app_embed = LangMessageable.app_send_embed
        self.app_send = LangMessageable.app_mod_send
        self.edit = LangMessageable.mod_edit
        self.color = discord.Colour.blurple()
        self.emojis_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '❌']
        self.emojis_dict = {
            '1️⃣': 0,
            "2️⃣": 1,
            "3️⃣": 2,
            "4️⃣": 3,
            "5️⃣": 4,
            "❌": -1
        }

    async def button_setup(self, msg, search):
        for emoji in list(self.emojis_list[:min(len(search), len(self.emojis_list))]):
            await msg.add_reaction(emoji)

        await msg.add_reaction("❌")

    @app_commands.command(name="join", description="Connection to the voice channel")
    async def join_voice(self, interaction: discord.Integration, channel: typing.Optional[discord.VoiceChannel] = None):
        if channel is None:
            try:
                member = interaction.guild.get_member(interaction.user.id)
                channel = member.voice.channel
            except AttributeError as e:
                return await self.app_send(interaction, "Failed to connect...", ephemeral=True)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is not None:
            if player.is_connected():
                return await self.app_send(interaction, "Bot is already connected to a voice channel", ephemeral=True)

        await channel.connect(cls=CustomPlayer(self.bot))
        await self.app_send(interaction, "Bot connect to the voice `%s`", format=(channel.name), ephemeral=True)

    @app_commands.command(name="leave", description="Disconnect to the voice channel")
    async def leave_voice(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        member = interaction.guild.get_member(interaction.user.id)
        member_bot = interaction.guild.get_member(self.bot.user.id)
        channel = member.voice

        if channel is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)
        elif channel.channel.id != member_bot.voice.channel.id:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        await player.disconnect()
        await self.app_send(interaction, "Disconnected..", ephemeral=True)

    @app_commands.command(name="play", description="Staring play sound from URL")
    async def play_command(self, interaction: discord.Integration, query: str):
        custom_player = CustomPlayer(self.bot)
        guild_id = interaction.guild.id
        member = interaction.guild.get_member(interaction.user.id)
        try:
            search = await wavelink.YouTubeTrack.search(query)
        except Exception as e:
            self.log.warning(f"Exception {e}", exc_info=e)
            return await self.send_app_embed(
                interaction,
                description="Something went wrong while searching for this track",
                color=discord.Colour.red()
            )

        if not search:
            return await self.app_send(interaction, "No tracks found", ephemeral=True)

        if member.voice is None:
            return await self.app_send(interaction, "first go to the voice channel, and then order the track",
                                       ephemeral=True)

        try:
            avatar = interaction.user.avatar.url
            author = {"name": "Select the track: ", "icon": avatar}
            await self.send_app_embed(
                interaction,
                description=("\n".join(f"**{i + 1}. {t.title}**" for i, t in enumerate(search[:5]))),
                color=self.color,
                author=author
            )
        except TypeError as e:
            self.log.warning(f"Exception {e}")
            author = {"name": "Something went wrong..", "icon": interaction.user.avatar}
            return await self.send_app_embed(
                interaction,
                description="The `/play` command cannot work with playlists, use `/playlistadd`",
                color=self.color,
                author=author
            )
        msg = await interaction.original_response()
        channel = msg.channel.id

        def check(res, user):
            return res.emoji in self.emojis_list and user == interaction.user and res.message.id == msg.id

        try:
            asyncio.run_coroutine_threadsafe(self.button_setup(msg, search), self.bot.loop)
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await msg.delete()
            return
        else:
            await msg.delete()

        try:
            if self.emojis_dict[reaction.emoji] == -1: 
                return
            choosed_track = search[self.emojis_dict[reaction.emoji]]
        except Exception as e:
            return self.log.error(e)

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await member.voice.channel.connect(cls=custom_player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        if vc.is_playing():
            vc.queue.put(item=choosed_track)
            author_play = {"name": "🎵 Add queue %s", "url": choosed_track.uri, "icon": interaction.user.avatar,
                           "format": choosed_track.title}
            await self.send_embed(
                channel,
                description="This added track in the queue\nNumber of music in the queue: **%s**",
                format={"description": len(vc.queue)},
                color=self.color,
                thumbnail=choosed_track.thumb,
                author=author_play
            )
        else:
            try:
                await vc.play(choosed_track)
            except Exception as e:
                self.log.error(e)
                return await self.send_embed(
                    channel,
                    title="Something went wrong while searching for this track",
                    color=discord.Color.red()
                )

            t_sec = int(choosed_track.length / 1000)
            hour = int(t_sec / 3600)
            mins = int((t_sec % 3600) / 60)
            sec = int((t_sec % 3600) % 60)
            length = f"{hour}:{mins}:{sec:02}" if not hour == 0 else f"{mins}:{sec:02}"
            author = {"name": "Now playing: %s", "icon": self.bot.user.avatar, "url": choosed_track.uri,
                      "format": choosed_track.title}
            fields = [
                {"name": "Artist:", "value": choosed_track.author, "inline": False},
                {"name": "Volume player:", "value": vc.volume, "inline": True},
                {"name": "Length", "value": length, "inline": True}
            ]
            await self.send_embed(
                channel,
                color=self.color,
                author=author,
                fields=fields,
                thumbnail=choosed_track.thumb
            )

    @app_commands.command(name="stop", description="Stop playing sound")
    async def stop_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        if player.is_playing:
            await player.stop()
            author = {"name": "Playback Stopped ⏹", "icon": interaction.user.avatar}
            await self.send_app_embed(
                interaction,
                description="You stopped the player, so you can start it again using `/play`",
                color=self.color,
                author=author,
                ephemeral=True
            )
        else:
            return await self.app_send(interaction, "Nothing Is playing right now", ephemeral=True)

    @app_commands.command(name="pause", description="Paused playback")
    async def pause_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        if not player.is_paused():
            if player.is_playing():
                await player.pause()
                author = {"name": "Playback Paused ⏸", "icon": interaction.user.avatar}
                await self.send_app_embed(
                    interaction,
                    description="The player is paused, to return it to work, use the `/resume` command",
                    color=self.color,
                    author=author,
                    ephemeral=True
                )
            else:
                return await self.app_send(interaction, "Nothing Is playing right now", ephemeral=True)
        else:
            return await self.app_send(interaction, "Playback is Already paused", ephemeral=True)

    @app_commands.command(name="resume", description="Playback resumed")
    async def resume_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)
        if player.is_paused():
            await player.resume()
            author = {"name": "Keeps playing", "icon": interaction.user.avatar}
            return await self.send_app_embed(
                interaction,
                description="Player is resume..",
                color=self.color,
                author=author,
                ephemeral=True
            )

        else:
            if not len(player.queue) == 0:
                track: wavelink.track = player.queue[0]
                await player.play(track)
                author = {"name": "Keeps playing", "icon": interaction.user.avatar}
                return await self.send_app_embed(
                    interaction,
                    description="Player is resume..",
                    color=self.color,
                    author=author,
                    ephemeral=True
                )
            else:
                return await self.app_send(interaction, "Playblack is not paused", ephemeral=True)

    @app_commands.command(name="volume", description="Playback volume")
    async def volume_command(self, interaction: discord.Integration, to: int):
        if to > 100:
            return await self.app_send(interaction, "Volume should between 0 and 100", ephemeral=True)
        elif to < 1:
            return await self.app_send(interaction, "Volume should between 0 and 100", ephemeral=True)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        await player.set_volume(to)
        await self.send_app_embed(
            interaction,
            title="Changed Volume to %s",
            format={"title": to},
            color=self.color,
            ephemeral=True
        )

    @app_commands.command(name="seek", description="Seek to the given position in the song.")
    async def seek_command(self, interaction: discord.Integration, seek: str):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        if not (match := re.match(TIME_REGEX, seek)):
            return await self.app_send(interaction, "Time code invalid", ephemeral=True)

        if match.group(3):
            secs = (int(match.group(1)) * 60) + (int(match.group(3)))
        else:
            secs = int(match.group(1))

        await player.seek(secs * 1000)
        await self.app_send(interaction, "Seeked", ephemeral=True)

    @app_commands.command(name="nowplaying", description="Now playing sound")
    async def now_play_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        if player.is_playing():
            t_sec = int(player.track.length / 1000)
            hour = int(t_sec / 3600)
            mins = int((t_sec % 3600) / 60)
            sec = int((t_sec % 3600) % 60)
            length = f"{hour}:{mins}:{sec:02}" if not hour == 0 else f"{mins}:{sec:02}"

            pos_sec = int(player.position / 1000)
            hour_pos = int(pos_sec / 3600)
            mins_pos = int((pos_sec % 3600) / 60)
            sec_pos = int((pos_sec % 3600) % 60)
            position = f"{hour_pos}:{mins_pos}:{sec_pos:02}" if not hour == 0 else f"{mins_pos}:{sec_pos:02}"

            if player.is_paused():
                text_paused = "Paused ⏸"
            else:
                text_paused = "Playing ▶"

            author = {"name": "Now playing:", "icon": interaction.user.avatar}

            fields = [
                {"name": "Track title", "value": f"[{player.track.info['title']}]({player.track.info['uri']})", "inline": False},
                {"name": "Artist", "value": player.track.info['author'], "inline": True},
                {"name": "Length", "value": f"{length}/{position}", "inline": True},
                {"name": "Volume Music", "value": f"{player.volume}%", "inline": True},
                {"name": "Player status", "value": text_paused, "inline": False}
            ]

            await self.send_app_embed(
                interaction,
                color=self.color,
                author=author,
                fields=fields,
                thumbnail=f"https://img.youtube.com/vi/{player.track.info['identifier']}/maxresdefault.jpg"
            )
        else:
            return await self.app_send(interaction, "Nothing is playing right now", ephemeral=True)

    @app_commands.command(name="skip", description="Skip playing music")
    async def skip_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player:
            format_title = (player.current.title, node.uri)
            author_format = (interaction.user.display_name)
            author = {"name": "User %s skipped track", "icon": interaction.user.avatar, "format": author_format}

            if not player.is_playing():
                return await self.app_send(interaction, "Nothing is playing", ephemeral=True)

            if player.queue.is_empty:
                await self.send_app_embed(
                    interaction,
                    description="Track: [%s](%s) has skip!",
                    format={"description": format_title},
                    author=author,
                    color=self.color,
                )

                return await player.stop()

            await self.send_app_embed(
                interaction,
                description="Track: [%s](%s) has skip!",
                format={"description": format_title},
                author=author,
                color=self.color
            )

            if player.is_paused():
                await player.resume()

            await player.seek(player.position * 1000)
        else:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

    @app_commands.command(name="queue", description="Show queue list")
    async def queue_command(self, interaction: discord.Integration):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.guild.id)

        if player is None:
            return await self.app_send(interaction, "Bot is not connected to any voice channel", ephemeral=True)

        if not player.queue.is_empty:
            queue_list = player.queue
            author = {"name": "Now playing %s" if player.is_playing() else "Queue: ", "icon": interaction.user.avatar, "format": player.current.title}
            return await self.send_app_embed(
                interaction,
                color=self.color,
                description="\n".join(f"**{i + 1}. {track}**" for i, track in enumerate(queue_list)),
                author=author
            )
        else:
            return await self.app_send(interaction, "The queue is empty", ephemeral=True)

    @app_commands.command(name="playlistadd", description="Playing playlist on YouTube")
    async def playlist_play_command(self, interaction: discord.Integration, playlist: str):
        try:
            search_playlist = await wavelink.YouTubeTrack.search(query=playlist)
        except Exception as e:
            self.log.warning(f"Exception {e}")
            return await self.send_app_embed(
                interaction,
                title="Something went wrong while searching for this track",
                color=discord.Color.red()
            )
        member = interaction.guild.get_member(interaction.user.id)

        if member.voice is None:
            return await self.app_send(interaction, "Go to voice chat, and then use this command again", ephemeral=True)

        if not interaction.guild.voice_client:
            custom_player = CustomPlayer()
            vc: wavelink.Player = await member.voice.channel.connect(cls=custom_player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        for tracks in search_playlist.tracks:
            vc.queue.put(item=tracks)

        if vc.is_playing():
            author_play = {"name": "🎵 Add queue %s", "url": search_playlist.uri, "icon": interaction.user.avatar,
                           "format": search_playlist.title}
            await self.send_app_embed(
                interaction,
                description="This added track in the queue\nNumber of music in the queue: **%s**",
                format={"description": len(vc.queue)},
                color=self.color,
                thumbnail=search_playlist.thumb,
                author=author_play
            )
        else:
            try:
                await vc.play(vc.queue.get())
                author_q = {"name": "🎵 Add queue playlist %s", "url": playlist, "icon": interaction.user.avatar,
                            "format": search_playlist.name}
                await self.send_app_embed(
                    interaction,
                    description="This added track in the queue\nNumber of music in the queue: **%s**",
                    thumbnail=search_playlist.tracks[0].thumb,
                    color=self.color,
                    author=author_q,
                    ephemeral=True
                )

                msg = await interaction.original_response()

                if self.only_channel(interaction.guild.id) is not None:
                    channel = self.db.music_channel_selector(guild_id=interaction.guild.id)
                else:
                    channel = self.bot.get_channel(msg.channel.id)

                t_sec = int(search_playlist.tracks[0].length)
                hour = int(t_sec / 3600)
                mins = int((t_sec % 3600) / 60)
                sec = int((t_sec % 3600) % 60)
                length = f"{hour}:{mins}:{sec:02}" if not hour == 0 else f"{mins}:{sec:02}"
                author = {"name": "Playing now %s", "icon": self.bot.user.avatar,
                          "format": search_playlist.tracks[0].title, "url": search_playlist.tracks[0].uri}
                fields = [
                    {"name": "Artist:", "value": f"{search_playlist.tracks[0].author}", "inline": False},
                    {"name": "Volume player:", "value": "{vc.volume} %", "inline": True},
                    {"name": "Length", "value": length, "inline": True},

                ]
                await self.send_embed(
                    channel,
                    color=self.color,
                    thumbnail=search_playlist.tracks[0].thumb,
                    author=author,
                    fields=fields
                )

                if self.channel.get(f"{interaction.guild.id}") is None:
                    self.channel.update({f"{interaction.guild.id}": channel})

            except Exception as e:
                self.log.error(e)
                return await self.send_app_embed(
                    interaction,
                    description="Something went wrong while searching for this track",
                    color=discord.Color.red()
                )
        
    @app_commands.command(name="music_set_channel", description="Sets the parameters where to send a message from the music functionality")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def m_set_channel(self, interaction: discord.Integration, channel: discord.TextChannel):
        await self.app_send(interaction, "Settings applied to this channel: `%s`", format=(channel.name))
        self.db.music_channel_update(guild_id=interaction.guild.id, channel_id=channel.id)

    @app_commands.command(name="music_channel_only", description="Enable sending messages to a special channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def m_channel_only(self, interaction: discord.Integration):
        guild = interaction.guild.id
        if self.db.music_channel_selector(guild_id=guild) is None:
            return await self.app_send(interaction, "You do not have a social channel set up, this can be done via `/music_set_channel`", ephemeral=True)
        if self.db.select_music_channel_only(guild_id=guild) == 0:
            self.db.update_music_channel_only(guild_id=guild, bool=True)
            await self.app_send(interaction, "Sending to a special channel, enabled")
        elif self.db.select_music_channel_only(guild_id=guild) == 1:
            self.db.update_music_channel_only(guild_id=guild, bool=False)
            await self.app_send(interaction, "Sending to a special channel, disabled")
   

async def setup(bot: commands.Bot):
    settings = config()
    await bot.add_cog(MusicCommand(bot), guilds=[discord.Object(id=settings['main_guild'])])