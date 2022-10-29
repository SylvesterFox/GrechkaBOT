import discord
import datetime
from discord.errors import NotFound
from asyncio import sleep
from discord import app_commands, utils
from database import init_bot_db, RolesDatabase
from settings_bot import config
from derpibooru import Search, sort

role_db = RolesDatabase()
settings = config()


class DiscordClient(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.synced = False

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
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=settings["main_guild"]))
        print(f"Буп!\nВы вошли как {self.user}")
        try:
            await self.setup_emoji()
        except Exception as e:
            print(e)

    async def on_raw_reaction_add(self, payload):
        if payload.emoji.id:
            emoji = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji = payload.emoji.name

        # data - [0] Role Id [1] Channel Id [2] Message post id
        data_db = role_db.db_role_get(guild_id=payload.guild_id, emoji=emoji)
        if data_db is None:
            return

        if self.user.id == payload.user_id:
            return
        if data_db[1] != payload.channel_id:
            return
        if data_db[2] != payload.message_id:
            return

        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = message.guild.get_member(payload.user_id)
        try:
            role = utils.get(message.guild.roles, id=data_db[0])
            await member.add_roles(role)
            print(f"[УСПЕХ] Пользователю {member.name} была выдана роль: {role.name}")
        except KeyError as e:
            print("[ОШИБКА] Ошибка ключа, не найдена роль для" + e)
        except AttributeError as e:
            print(f"[ОШИБКА] Атрибут роли не найден, похоже, что его больше нет на сервере, или он был удален:\n {e}")
            print("[Внимание] Настройки этой роли будут удалены из базы данных.")
            await sleep(10.0)
            _ = role_db.db_role_delete(role_id=data_db[0])
            await message.remove_reaction(payload.emoji, member=self.user)
        except Exception as e:
            print(repr(e))

    async def on_raw_reaction_remove(self, payload):
        if payload.emoji.id:
            emoji = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji = payload.emoji.name

        # data - [0] Role Id [1] Channel Id [2] Message post id
        data_db = role_db.db_role_get(guild_id=payload.guild_id, emoji=emoji)
        if data_db is None:
            return

        if self.user.id == payload.user_id:
            return
        if data_db[1] != payload.channel_id:
            return
        if data_db[2] != payload.message_id:
            return

        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = message.guild.get_member(payload.user_id)
        try:
            role = utils.get(message.guild.roles, id=data_db[0])
            await member.remove_roles(role)
            print(f"[УСПЕХ] У пользователя {member.name} была удалена роль: {role.name}")
        except KeyError as e:
            print("[ОШИБКА] Ошибка ключа, не найдена роль для " + e)
        except AttributeError as e:
            print(f"[ОШИБКА] Атрибут роли не найден, похоже, что его больше нет на сервере, или он был удален:\n {e}")
            print("[Внимание] Настройки этой роли будут удалены из базы данных через 10 секунд.")
            await sleep(10.0)
            _ = role_db.db_role_delete(role_id=data_db[0])
            await message.clear_reaction(payload.emoji)
        except Exception as e:
            print(repr(e))


intents = discord.Intents.default()
intents.members = True
client = DiscordClient(intents=intents)
tree = app_commands.CommandTree(client)


# Command
@tree.command(name="reactroleadd", description="Создаёт реакцию под сообщением для получения роли.",
              guild=discord.Object(id=settings["main_guild"]))
@app_commands.checks.has_permissions(administrator=True)
async def self(interaction: discord.Integration, channel: discord.TextChannel, id_message: str, emoji: str,
               role: discord.Role):
    try:
        message = await channel.fetch_message(int(id_message))
        role_db.role_insert(guild_id=interaction.guild.id, channel_id=channel.id, message_id=int(id_message), emoji=emoji,
                            role_id=role.id)
        await message.add_reaction(emoji)
        await interaction.response.send_message(
            f"✅ `[УСПЕХ]` Получаемая роль: {role.mention}\n"
            f"Реакция для получения роли: {emoji}"
            f" на этом сообщении [Message](https://discord.com/channels/{interaction.guild.id}/{channel.id}/{id_message})",
            ephemeral=True)
    except NotFound as e:
        await interaction.response.send_message(f"💢 [ОШИБКА] {e}", ephemeral=True)


@tree.command(name="reactroleremove", description="Удаляет реакцию на получение роли.",
              guild=discord.Object(id=settings["main_guild"]))
@app_commands.checks.has_permissions(administrator=True)
async def self(interaction: discord.Integration, role: discord.Role):
    data = role_db.db_role_delete(role_id=role.id)
    if data is None:
        await interaction.response.send_message("⚠ `[Внимание]` Эта роль большне не существует или уже удалена из базы данных.", ephemeral=True)
        return
    channel = client.get_channel(data[1])
    message = await channel.fetch_message(data[0])
    await message.clear_reaction(emoji=data[2])
    await interaction.response.send_message(f"✅ `[УСПЕХ]` Роль выдачи {role.mention} была успешно удалена.", ephemeral=True)
    
@tree.command(name="mlp-nsfw-random", description="Тест рассылки NSFW контента.",
              guild=discord.Object(id=settings["main_guild"]))
@app_commands.checks.has_permissions(administrator=True)
async def self(interaction: discord.Integration):
    for image in Search(filter_id='37432').sort_by(sort.RANDOM).limit(1):
        await interaction.response.send_message(f"✅ Кринж был успешно запощен.\n" + image.url, ephemeral=False)
        now = datetime.datetime.now()
        print(f"✅ Кринж был успешно запощен.", now.time(), "-", image.url)

@tree.command(name="mlp-nsfw-tag", description="Тест рассылки NSFW контента 2.",
              guild=discord.Object(id=settings["main_guild"]))
@app_commands.checks.has_permissions(administrator=True)
async def self(interaction: discord.Integration, tag1: str, tag2: str, tag3: str, tag4: str,):
    for image in Search(filter_id='37432').query(tag1, tag2, tag3, tag4).limit(1):
        await interaction.response.send_message(f"✅ Кринж был успешно запощен.\n" + image.url, ephemeral=False)
        now = datetime.datetime.now()
        print(f"✅ Кринж был успешно запощен.", now.time(), "-", image.url)

@tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(error, ephemeral=True)
    else:
        raise error
