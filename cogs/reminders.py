import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from models.database import Database
from utils.views import DeletableDropdown
from utils.helpers import validate_date_format, validate_time_format

class ReminderModal(discord.ui.Modal, title='Set New Reminder'):
    date = discord.ui.TextInput(
        label='Date (YYYY-MM-DD)',
        placeholder='2025-07-10',
        required=True,
        max_length=10
    )

    time = discord.ui.TextInput(
        label='Time (HH:MM)',
        placeholder='02:31',
        required=True,
        max_length=5
    )

    message = discord.ui.TextInput(
        label='Reminder Message',
        placeholder='What should I remind you about?',
        style=discord.TextStyle.long,
        required=True,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not validate_date_format(self.date.value):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Date Format",
                    description="Please use YYYY-MM-DD format (e.g., 2025-07-10)",
                    color=0xff0000
                ),
                ephemeral=True
            )

        if not validate_time_format(self.time.value):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Time Format",
                    description="Please use HH:MM format (e.g., 02:31)",
                    color=0xff0000
                ),
                ephemeral=True
            )

        try:
            offset = await Database.get_user_timezone(interaction.user.id)

            user_dt = datetime.strptime(
                f"{self.date.value} {self.time.value}",
                "%Y-%m-%d %H:%M"
            )

            now = datetime.now()
            remind_time = user_dt - timedelta(hours=offset)

            if remind_time < now:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Time Travel Error",
                        description="You can't set reminders in the past!",
                        color=0xff0000
                    ),
                    ephemeral=True
                )
        except ValueError as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Date/Time Error",
                    description=f"Invalid date/time: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

        try:
            await Database.add_reminder(
                interaction.user.id,
                self.message.value,
                remind_time.isoformat() + 'Z'
            )
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error Setting Reminder",
                    description=f"Failed to set reminder: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

        local_time = user_dt.strftime("%Y-%m-%d %H:%M")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Reminder Set",
                description=f"I'll remind you on **{local_time}** about:\n{self.message.value}",
                color=0x00ff00
            )
        )

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    reminder = app_commands.Group(name="reminder", description="Manage your reminders")

    @reminder.command(name="add", description="Set a new reminder")
    async def reminder_add(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReminderModal())

    @reminder.command(name="list", description="View your reminders")
    async def reminder_list(self, interaction: discord.Interaction):
        try:
            offset = await Database.get_user_timezone(interaction.user.id)
            reminders = await Database.get_reminders(interaction.user.id)
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"Failed to fetch reminders: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

        if not reminders:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏰ Your Reminders",
                    description="You have no reminders set!",
                    color=0xffffff
                )
            )

        formatted_reminders = []
        for r in reminders:
            utc_time = datetime.fromisoformat(r['remind_at'].replace('Z', '+00:00'))
            local_time = (utc_time + timedelta(hours=offset)).strftime('%Y-%m-%d %H:%M')
            formatted_reminders.append(f"`{local_time}` - {r['message']}")

        desc = "\n".join(f"{i+1}. {r}" for i, r in enumerate(formatted_reminders))

        view = DeletableDropdown(reminders, is_task=False)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"⏰ Your Reminders ({len(reminders)})",
                description=desc,
                color=0xffffff
            ),
            view=view
        )

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        from utils.helpers import get_utc_timestamps

        one_min_ago_str, now_str = get_utc_timestamps()

        try:
            reminders = await Database.get_due_reminders(one_min_ago_str, now_str)
        except Exception as e:
            print(f"Failed to fetch reminders: {e}")
            return

        for reminder in reminders:
            user_id = reminder["user_id"]
            message = reminder["message"]
            try:
                user = await self.bot.fetch_user(user_id)
                embed = discord.Embed(
                    title="🔔 Reminder",
                    description=message,
                    color=0xffffff
                )
                await user.send(embed=embed)
            except Exception as e:
                print(f"Failed to send reminder to {user_id}: {e}")

        for reminder in reminders:
            try:
                rid = reminder.get("id")
                if rid:
                    await Database.delete_reminder(rid)
            except Exception as e:
                print(f"Failed to delete reminder {rid}: {e}")

    def cog_unload(self):
        self.check_reminders.cancel()

async def setup(bot):
    await bot.add_cog(Reminders(bot))
