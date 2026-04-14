import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 123456789012345678  # ←ここに自分のサーバーID

# -------------------------
# 作成コマンド
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(
    name="create-room",
    description="ロールごとに部屋を作成",
    guild=discord.Object(id=GUILD_ID)  # ←ギルド限定
)
@app_commands.describe(
    role="部屋を作るロールを選択",
    limit="ボイスの人数制限（未入力で無制限）"
)
async def create_room(interaction: discord.Interaction, role: str, limit: int = None):

    guild = interaction.guild
    role = guild.get_role(int(role))

    if not role:
        await interaction.response.send_message("ロールが見つからない！", ephemeral=True)
        return

    if discord.utils.get(guild.categories, name=role.name):
        await interaction.response.send_message(
            f"⚠️ {role.name}のカテゴリは既に存在します！",
            ephemeral=True
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role: discord.PermissionOverwrite(view_channel=True)
    }

    category = await guild.create_category(role.name, overwrites=overwrites)
    await guild.create_text_channel("チャット", category=category)

    if limit:
        await guild.create_voice_channel("通話", category=category, user_limit=limit)
    else:
        await guild.create_voice_channel("通話", category=category)

    await interaction.response.send_message(
        f"✅ {role.name}の部屋を作成！（人数制限: {limit if limit else 'なし'}）",
        ephemeral=True
    )

# -------------------------
# 削除コマンド
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(
    name="delete-room",
    description="ロールの部屋を削除",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(role="削除するロール")
async def delete_room(interaction: discord.Interaction, role: str):

    guild = interaction.guild
    role = guild.get_role(int(role))

    if not role:
        await interaction.response.send_message("ロールが見つからない！", ephemeral=True)
        return

    category = discord.utils.get(guild.categories, name=role.name)

    if not category:
        await interaction.response.send_message(
            "❌ そのカテゴリは存在しない！",
            ephemeral=True
        )
        return

    for channel in category.channels:
        await channel.delete()

    await category.delete()

    await interaction.response.send_message(
        f"🗑️ {role.name}の部屋を削除したよ！",
        ephemeral=True
    )

# -------------------------
# autocomplete
# -------------------------
@create_room.autocomplete("role")
async def create_room_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=role.name, value=str(role.id))
        for role in interaction.guild.roles
        if not role.is_default()
        and current.lower() in role.name.lower()
    ][:25]


@delete_room.autocomplete("role")
async def delete_room_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=role.name, value=str(role.id))
        for role in interaction.guild.roles
        if not role.is_default()
        and current.lower() in role.name.lower()
    ][:25]

# -------------------------
# 起動時（完全同期）
# -------------------------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    bot.tree.clear_commands(guild=guild)  # ←古いコマンド削除
    await bot.tree.sync(guild=guild)      # ←強制上書き

    print(f"完全同期完了: {bot.user}")

# -------------------------
# エラー処理
# -------------------------
@create_room.error
@delete_room.error
async def error_handler(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ 管理者のみ使用できます",
            ephemeral=True
        )

# -------------------------
# 起動
# -------------------------
bot.run(os.getenv("TOKEN"))
