import discord 
import wavelink
import typing
from discord.ext import commands
from discord import app_commands
from settings_bot import config

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.create_node())

    async def create_node(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot, host="127.0.0.1", port="2333", password="youshallnotpass", region="europe")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node: <{node.identifier}> is now Ready!")

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

    @app_commands.command(name="stop", description="Disconnect to the voice channel")
    async def stop_voice(self, interaction: discord.Integration):
        voice_connect = interaction.guild.voice_client
        await voice_connect.disconnect()
        await interaction.response.send_message("Disconnect..", ephemeral=True)
        
    @stop_voice.error
    async def stop_commnd_error(self, interaction, error):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message("The bot no longer exists in your channels", ephemeral=True)
        else:
            raise error



async def setup(bot: commands.Bot):
    settings = config()
    await bot.add_cog(Music(bot), guilds=[discord.Object(id=settings['main_guild']), discord.Object(id=617020672929169418)])