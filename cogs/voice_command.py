import discord
from core.settings_bot import config
from discord.ext import commands
from discord import app_commands
from core.database import VcDB


class VoiceCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vc_db = VcDB()

    @app_commands.command(name="vcsetup")
    @app_commands.checks.has_permissions(administrator=True)
    async def voice_setup(self, interaction: discord.Interaction):
        if self.vc_db.get_lobby_from_guild(guild_id=interaction.guild.id) is not None:
            print(self.vc_db.get_lobby_from_guild(guild_id=interaction.guild.id))
            return await interaction.response.send_message("You already have a lobby")
        mbed = discord.Embed(
            title="Success!",
            description=f"A lobby has been created on your server to create voice channels ✅",
            color=discord.Color.green()
        )
        vc = await interaction.guild.create_voice_channel(name="[+] Create Voice Channel [+]")
        await interaction.response.send_message(embed=mbed)
        self.vc_db.vc_setup_insert(guild_id=interaction.guild.id, voice_channel_id=vc.id)


async def setup(bot: commands.Bot):
    settings = config()
    await bot.add_cog(VoiceCommand(bot), guilds=[discord.Object(id=settings['main_guild'])])
