import discord
import logging
from random import choice
from discord.ext import commands, tasks
from database import init_bot_db, RolesDatabase
from settings_bot import config

role_db = RolesDatabase()
settings = config()


class DiscordClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        self.log = logging.getLogger('LunaBot')
        super().__init__(
            command_prefix=settings["prefix"],
            intents=intents)

    @tasks.loop(seconds=60.0)
    async def status(self):
        status = settings['game_activity']
        random_activity = choice(status)
        
        match random_activity['activity']:
            case "game":
                await self.change_presence(activity=discord.Game(name=random_activity['name']))
            case "listening":
                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                                     name=random_activity['name']))
            case "watching":
                await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                     name=random_activity['name']))

    async def setup_hook(self):
        for extend in settings['extension']:
            await self.load_extension(extend)
            self.log.info(f"Load - {extend}")
        await self.tree.sync(guild = discord.Object(id = settings["main_guild"]))
        # await self.tree.sync(guild=discord.Object(id=617020672929169418)) # это для дебага
        self.log.info(f"Synced slash commands for {self.user}")

    async def setup_emoji(self):
        channel_db = role_db.db_channel_id()
        if len(channel_db) == 0:
            return
        for row in channel_db:
            channel = self.get_channel(row[0])
            message = await channel.fetch_message(row[1])
            await message.add_reaction(row[2])
    
    async def on_ready(self):
        init_bot_db()
        print(f"Буп!\nВы вошли как {self.user}")
        self.status.start()

        try:
            await self.setup_emoji()
        except Exception as e:
            self.log.error(e)


client = DiscordClient()
        