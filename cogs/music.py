import discord
import wavelink
import logging
import datetime as dt

from discord.ext import commands
from core.settings_bot import config
from core.custom import LangMessageable
from core.database import GuildSettings


URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s(" \
            r")<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])) "


class CustomPlayer(wavelink.Player):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.queue = wavelink.BaseQueue()
        self.bot = bot


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger(f'LunaBOT.{__name__}')
        self.db = GuildSettings()
        self.send = LangMessageable.mod_send
        self.send_embed = LangMessageable.send_embed
        self.send_app_embed = LangMessageable.app_send_embed
        self.app_send = LangMessageable.app_mod_send
        self.edit = LangMessageable.mod_edit
        self.color = discord.Colour.blurple()
        bot.loop.create_task(self.create_node())

    async def create_node(self):
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        self.log.info(f"Node: <{node.id}> is now Ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        player = CustomPlayer(self.bot)
        channel = None

        # if payload.reason == "STOPPED":
        #     author = {"name": "Queue is over..", "icon": self.bot.user.avatar}
        #     await self.send_embed(
        #         channel,
        #         color=discord.Colour.blurple(),
        #         description="To extend, order more music through the `/play` command",
        #         author=author
        #     )
        #     player.queue.clear()
        #
        # if not player.queue.is_empty:
        #     next_track = player.queue.get()
        #     await player.play(next_track)
        #     t_sec = int(next_track.length)
        #     hour = int(t_sec / 3600)
        #     mins = int((t_sec % 3600) / 60)
        #     sec = int((t_sec % 3600) % 60)
        #     length = f"{hour}:{mins}:{sec:02}" if not hour == 0 else f"{mins}:{sec:02}"
        #     author = {"name": "Now playing:", "icon": self.bot.user.avatar }
        #     fields = [
        #         {"name": "Track title", "value": f"[{next_track.info['title']}]({next_track.info['uri']})", "inline": False},
        #         {"name": "Artist", "value": next_track.info['author'], "inline": True},
        #         {"name": "Length", "value": length, "inline": True}
        #
        #     ]
        #     await self.send_embed(
        #         channel,
        #         color=discord.Colour.blurple(),
        #         author=author,
        #         fields=fields,
        #         thumbnail=f"https://img.youtube.com/vi/{next_track.info['identifier']}/maxresdefault.jpg"
        #     )
        # else:
        #     if payload.reason == "FINISHED":
        #         author = {"name": "Queue is over..", "icon": self.bot.user.avatar }
        #         await self.send_embed(
        #             channel,
        #             color=discord.Colour.blurple(),
        #             description="To extend, order more music through the `/play` command",
        #             author=author
        #         )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                node = wavelink.NodePool.get_node()
                player = node.get_player(member.guild.id)
                if player:
                    await player.disconnect()

        elif member.bot and before.channel:
            if not [m for m in before.channel.members if m is None]:
                return
            node = wavelink.NodePool.get_node()
            player = node.get_player(member.guild.id)
            await player.disconnect()

            

async def setup(bot: commands.Bot):
    settings = config()
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=settings['main_guild'])])
