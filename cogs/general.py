import discord
from discord import app_commands
from discord.ext import commands
from models.database import Database

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows command information")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="📔 Taskforce Guide",
                description=
                    '''
                    __General Commands__
                    `/help` - Shows this message
                    `/set_timezone [UTC offset]` - Set your timezone offset from UTC (e.g. -5, 0, 2)

                    __Task Commands__
                    `/task add` - Add a task with a certain priority from 1 to 3
                    `/task list` - View all your tasks

                    __Reminder Commands__
                    `/reminder add` - Set a reminder for a certain time
                    `/reminder list` - View all your reminders

                    __Pomodoro Commands__
                    `/pomodoro start` - Start a Pomodoro session
                    `/pomodoro stop` - Stop your current Pomodoro session
                    `/pomodoro status` - View the status of your current Pomodoro session
                    `/pomodoro settings` - View or change your Pomodoro settings''',
                color=0xffffff
            ).set_footer(
                text="Notice: This bot is in beta and may have bugs."
            ),
            ephemeral=True
        )

    @app_commands.command(name="set_timezone", description="Set your timezone offset from UTC")
    @app_commands.describe(offset="Your UTC offset in hours (e.g., -5 for EST, 0 for UTC, 2 for EET)")
    async def set_timezone(self, interaction: discord.Interaction, offset: int):
        if offset < -12 or offset > 14:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="Offset must be between -12 and +14",
                    color=0xff0000
                ),
                ephemeral=True
            )

        try:
            await Database.set_user_timezone(interaction.user.id, offset)
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"Failed to set timezone: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Timezone Set",
                description=f"Your timezone offset is now UTC {offset:+d}",
                color=0x00ff00
            )
        )

async def setup(bot):
    await bot.add_cog(General(bot))
