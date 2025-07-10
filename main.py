import os
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord import Intents
from discord.ui import View, Select

from datetime import datetime, timedelta, timezone
import httpx
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

bot = commands.Bot(command_prefix='!', intents=Intents.all())

# ======================
# MODAL CLASSES
# ======================

class TaskModal(discord.ui.Modal, title='Add New Task'):
    task = discord.ui.TextInput(
        label='Task Description',
        placeholder='What do you need to do?',
        style=discord.TextStyle.long,
        required=True,
        max_length=200
    )

    priority = discord.ui.TextInput(
        label='Priority (1-3)',
        placeholder='Enter 1 (high), 2 (medium), or 3 (low)',
        required=True,
        max_length=1
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.priority.value not in ('1', '2', '3'):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Priority",
                    description="Priority must be 1, 2, or 3",
                    color=0xff0000
                ),
                ephemeral=True
            )

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{SUPABASE_URL}/rest/v1/tasks",
                    headers=HEADERS,
                    json={
                        "user_id": int(interaction.user.id),
                        "task": self.task.value,
                        "priority": int(self.priority.value)
                    }
                )
                res.raise_for_status()
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error Adding Task",
                    description=f"Failed to add task: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Task Added",
                description=f"**{self.task.value}** (Priority {self.priority.value})",
                color=0x00ff00
            )
        )

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
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', self.date.value):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Date Format",
                    description="Please use YYYY-MM-DD format (e.g., 2025-07-10)",
                    color=0xff0000
                ),
                ephemeral=True
            )

        if not re.match(r'^\d{2}:\d{2}$', self.time.value):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Time Format",
                    description="Please use HH:MM format (e.g., 02:31)",
                    color=0xff0000
                ),
                ephemeral=True
            )

        user_id = int(interaction.user.id)
        try:
            async with httpx.AsyncClient() as client:
                tz_res = await client.get(
                    f"{SUPABASE_URL}/rest/v1/timezones?user_id=eq.{user_id}",
                    headers=HEADERS
                )
                tz_res.raise_for_status()
                offset = tz_res.json()[0]["utc_offset"] if tz_res.json() else 0
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Timezone Error",
                    description=f"Failed to get your timezone: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

        try:
            user_dt = datetime.strptime(
                f"{self.date.value} {self.time.value}",
                "%Y-%m-%d %H:%M"
            )

            now = datetime.now(timezone.utc).replace(tzinfo=None)
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
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{SUPABASE_URL}/rest/v1/reminders",
                    headers=HEADERS,
                    json={
                        "user_id": user_id,
                        "message": self.message.value,
                        "remind_at": remind_time.isoformat() + 'Z'
                    }
                )
                res.raise_for_status()
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

# ======================
# BOT COMMANDS & EVENTS
# ======================

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user.name} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    check_reminders.start()

@tasks.loop(minutes=1)
async def check_reminders():
    now = datetime.now(timezone.utc)
    one_min_ago = now - timedelta(minutes=1)

    one_min_ago_str = one_min_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{SUPABASE_URL}/rest/v1/reminders?remind_at=gt.{one_min_ago_str}&remind_at=lte.{now_str}",
                headers=HEADERS
            )
            res.raise_for_status()
            reminders = res.json()
        except Exception as e:
            print(f"Failed to fetch reminders: {e}")
            return

        for reminder in reminders:
            user_id = reminder["user_id"]
            message = reminder["message"]
            try:
                user = await bot.fetch_user(user_id)
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
                    await client.delete(
                        f"{SUPABASE_URL}/rest/v1/reminders?id=eq.{rid}",
                        headers=HEADERS
                    )
            except Exception as e:
                print(f"Failed to delete reminder {rid}: {e}")

@bot.tree.command(name="help", description="Shows command information")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=discord.Embed(
            title="📔 Taskforce Guide",
            description=
                '''
                __General Commands__
                `/help` - Shows this message
                `/set_timezone [UTC offset]` - Set your timezone offset from UTC (e.g. -5, 0, 2)

                __Task Commands__
                `/task add [task] [priority]` - Add a task with a certain priority from 1 to 3
                `/task list` - View all your tasks

                __Reminder Commands__
                `/reminder add [time] [message]` - Set a reminder for a certain time
                `/reminder list` - View all your reminders''',
            color=0xffffff
        ).set_footer(
            text="Notice: This bot is in beta and may have bugs.",
        ),
        ephemeral=True
    )

class DeletableDropdown(View):
    def __init__(self, data, is_task: bool):
        super().__init__()
        self.add_item(self.DeletionSelect(data, is_task))

    class DeletionSelect(Select):
        def __init__(self, data, is_task):
            options = [
                discord.SelectOption(
                    label=f"{i+1}. {d['task'][:45] + '...' if len(d.get('task', '')) > 45 else d.get('task', '')}",
                    value=str(d["id"])
                ) if is_task else discord.SelectOption(
                    label=f"{i+1}. {d['message'][:45] + '...' if len(d.get('message', '')) > 45 else d.get('message', '')}",
                    value=str(d["id"])
                )
                for i, d in enumerate(data)
            ]
            placeholder = "Select a task to delete" if is_task else "Select a reminder to delete"
            super().__init__(placeholder=placeholder, options=options, min_values=1, max_values=1)
            self.data = data
            self.is_task = is_task

        async def callback(self, interaction: discord.Interaction):
            target_id = self.values[0]
            table = "tasks" if self.is_task else "reminders"
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.delete(
                        f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{target_id}",
                        headers=HEADERS
                    )
                    res.raise_for_status()
            except Exception as e:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description=f"Failed to delete: {e}",
                        color=0xff0000
                    ),
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🗑️ Deleted",
                    description="Successfully removed!",
                    color=0x00ff00
                ),
                ephemeral=True
            )

task = app_commands.Group(name="task", description="Manage your tasks")

@task.command(name="add", description="Add a new task")
async def task_add(interaction: discord.Interaction):
    await interaction.response.send_modal(TaskModal())

@task.command(name="list", description="View your tasks")
async def task_list(interaction: discord.Interaction):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{SUPABASE_URL}/rest/v1/tasks?user_id=eq.{int(interaction.user.id)}",
                headers=HEADERS
            )
            res.raise_for_status()
            tasks = res.json()
    except Exception as e:
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Error",
                description=f"Failed to fetch tasks: {e}",
                color=0xff0000
            ),
            ephemeral=True
        )

    if not tasks:
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="📝 Your Tasks",
                description="You have no tasks! 🎉",
                color=0xffffff
            )
        )

    desc = "\n".join(
        f"{i+1}. **{t['task']}** (Priority {t['priority']})"
        for i, t in enumerate(tasks)
    )

    view = DeletableDropdown(tasks, is_task=True)
    await interaction.response.send_message(
        embed=discord.Embed(
            title=f"📝 Your Tasks ({len(tasks)})",
            description=desc,
            color=0xffffff
        ),
        view=view
    )

reminder = app_commands.Group(name="reminder", description="Manage your reminders")

@reminder.command(name="add", description="Set a new reminder")
async def reminder_add(interaction: discord.Interaction):
    await interaction.response.send_modal(ReminderModal())

@reminder.command(name="list", description="View your reminders")
async def reminder_list(interaction: discord.Interaction):
    user_id = int(interaction.user.id)
    try:
        async with httpx.AsyncClient() as client:
            tz_res = await client.get(
                f"{SUPABASE_URL}/rest/v1/timezones?user_id=eq.{user_id}",
                headers=HEADERS
            )
            tz_res.raise_for_status()
            offset = tz_res.json()[0]["utc_offset"] if tz_res.json() else 0

            res = await client.get(
                f"{SUPABASE_URL}/rest/v1/reminders?user_id=eq.{user_id}",
                headers=HEADERS
            )
            res.raise_for_status()
            reminders = res.json()
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

@bot.tree.command(name="set_timezone", description="Set your timezone offset from UTC")
@app_commands.describe(offset="Your UTC offset in hours (e.g., -5 for EST, 0 for UTC, 2 for EET)")
async def set_timezone(interaction: discord.Interaction, offset: int):
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
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{SUPABASE_URL}/rest/v1/timezones",
                headers=HEADERS,
                json={"user_id": int(interaction.user.id), "utc_offset": offset},
                params={"on_conflict": "user_id"}
            )
            res.raise_for_status()
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

bot.tree.add_command(task)
bot.tree.add_command(reminder)

bot.run(TOKEN)
