import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# 作成コマンド
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="create-room", description="ロールごとに部屋を作成")
@app_commands.describe(role="部屋を作るロールを選択")
async def create_room(interaction: discord.Interaction, role: discord.Role):

    guild = interaction.guild

    # 既に存在チェック
    if discord.utils.get(guild.categories, name=role.name):
        await interaction.response.send_message(
            f"⚠️ {role.name}のカテゴリは既に存在します！",
            ephemeral=True
        )
        return

    # 権限設定
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role: discord.PermissionOverwrite(view_channel=True)
    }

    # 作成
    category = await guild.create_category(role.name, overwrites=overwrites)
    await guild.create_text_channel("チャット", category=category)
    await guild.create_voice_channel("通話", category=category)

    await interaction.response.send_message(
        f"✅ {role.name}の部屋を作成したよ！",
        ephemeral=True
    )

# -------------------------
# 削除コマンド
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="delete-room", description="ロールの部屋を削除")
@app_commands.describe(role="削除するロール")
async def delete_room(interaction: discord.Interaction, role: discord.Role):

    guild = interaction.guild
    category = discord.utils.get(guild.categories, name=role.name)

    if not category:
        await interaction.response.send_message(
            "❌ そのカテゴリは存在しない！",
            ephemeral=True
        )
        return

    # 中のチャンネル削除
    for channel in category.channels:
        await channel.delete()

    # カテゴリ削除
    await category.delete()

    await interaction.response.send_message(
        f"🗑️ {role.name}の部屋を削除したよ！",
        ephemeral=True
    )

# -------------------------
# 🔽 ここから追加（フィルター）
# -------------------------

# 作成用：まだ作ってないロールだけ表示
@create_room.autocomplete("role")
async def create_room_autocomplete(interaction: discord.Interaction, current: str):
    choices = []
    for role in interaction.guild.roles:
        if role.is_default():
            continue

        # 既にカテゴリあるロールは除外
        if discord.utils.get(interaction.guild.categories, name=role.name):
            continue

        if current.lower() in role.name.lower():
            choices.append(
                app_commands.Choice(name=role.name, value=role.id)
            )

    return choices[:25]


# 削除用：すでにあるロールだけ表示
@delete_room.autocomplete("role")
async def delete_room_autocomplete(interaction: discord.Interaction, current: str):
    choices = []
    for role in interaction.guild.roles:
        if role.is_default():
            continue

        # カテゴリがあるロールだけ
        if not discord.utils.get(interaction.guild.categories, name=role.name):
            continue

        if current.lower() in role.name.lower():
            choices.append(
                app_commands.Choice(name=role.name, value=role.id)
            )

    return choices[:25]

# -------------------------
# 起動時
# -------------------------
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"コマンド同期完了: {len(synced)}個")
    except Exception as e:
        print(e)

    print(f"ログイン完了: {bot.user}")

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
