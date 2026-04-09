import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# セレクトメニュー
# -------------------------
class RoleSelect(discord.ui.Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles if not role.is_default()
        ]

        super().__init__(
            placeholder="ロールを選択",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role_id = int(self.values[0])
        role = guild.get_role(role_id)

        # 同じカテゴリがあるか確認
        existing = discord.utils.get(guild.categories, name=role.name)
        if existing:
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

        # カテゴリ作成（ロール名）
        category = await guild.create_category(role.name, overwrites=overwrites)

        # テキストチャンネル「チャット」
        await guild.create_text_channel("チャット", category=category)

        # ボイスチャンネル「通話」
        await guild.create_voice_channel("通話", category=category)

        await interaction.response.send_message(
            f"✅ {role.name}用の部屋を作成したよ！",
            ephemeral=True
        )

# -------------------------
# View
# -------------------------
class RoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=60)
        self.add_item(RoleSelect(roles))

# -------------------------
# スラッシュコマンド
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="create-room", description="ロールごとに部屋を作成")
async def create_room(interaction: discord.Interaction):
    roles = interaction.guild.roles

    view = RoleView(roles)

    await interaction.response.send_message(
        "ロールを選択してね！",
        view=view,
        ephemeral=True
    )

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
async def create_room_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ 管理者のみ使用できます",
            ephemeral=True
        )

# -------------------------
# 起動
# -------------------------
bot.run(os.getenv("TOKEN"))