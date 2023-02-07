import discord
from core.database import VcDB
from discord.ext import commands


class VoiceEvent(commands.Cog):
    def __int__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        if after.channel is not None and before.channel is None:
            vc_db = VcDB()
            category = None
            if after.channel.category_id is not None:
                category = discord.utils.get(member.guild.categories, id=after.channel.category_id)

            if vc_db.get_lobby_from_guild(guild_id=member.guild.id) == after.channel.id:
                vc = await member.guild.create_voice_channel(name=f"Voice Lair {member.display_name}",
                                                             category=category)
                vc_db.create_vc(vc_id=vc.id,
                                name=vc.name,
                                created_at=member.display_name,
                                created_member_id=member.id,
                                guild_id=member.guild.id)
                await member.move_to(vc)
        elif before.channel is not None and after.channel is None:
            vc_db = VcDB()
            voice_channel = discord.utils.get(member.guild.channels, id=before.channel.id)
            members_count = len(voice_channel.members)
            if members_count == 0:
                name = vc_db.get_vcdb_name(channel_id=before.channel.id, guild_id=member.guild.id)
                if name is not None:
                    vc_db.delete_vc(channel_id=before.channel.id, guild_id=member.guild.id)
                    await voice_channel.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceEvent(bot))
