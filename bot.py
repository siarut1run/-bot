import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# ボタンUI
# -------------------------
class CreateRoomView(discord.ui.View):
    def __init__(self, role_id: int, limit: int):
        super().__init__(timeout=60)
        self.role_id = role_id
        self.limit = limit

    @discord.ui.button(label="部屋を作成", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role = guild.get_role(self.role_id)

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

        if self.limit:
            await guild.create_voice_channel("通話", category=category, user_limit=self.limit)
        else:
            await guild.create_voice_channel("通話", category=category)

        await interaction.response.send_message(
            f"✅ {role.name}の部屋を作成！（人数制限: {self.limit if self.limit else 'なし'}）",
            ephemeral=True
        )

# -------------------------
# 作成コマンド（UI版）
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="create-room", description="ロールごとに部屋を作成")
@app_commands.describe(
    role="ロールを選択",
    limit="ボイス人数制限（未入力で無制限）"
)
async def create_room(interaction: discord.Interaction, role: str, limit: int = None):

    role_id = int(role)

    view = CreateRoomView(role_id, limit)

    await interaction.response.send_message(
        "👇 ボタンを押すと部屋が作成されます",
        view=view,
        ephemeral=True
    )

# -------------------------
# 削除コマンド
# -------------------------
@app_commands.checks.has_permissions(administrator=True)
@bot.tree.command(name="delete-room", description="ロールの部屋を削除")
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
# 起動
# -------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"起動完了: {bot.user}")

bot.run(os.getenv("TOKEN"))
