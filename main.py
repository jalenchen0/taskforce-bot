import os
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands
from discord import Intents, Client, Message

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents=Intents.all())

@bot.event
async def on_ready():
    print("Bot is ready")
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="help", description="Shows command information")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Taskforce Guide",
            description=
                f'''
                __General Commands__
                `/help` - Shows this message

                __Task Commands__
                `/task add [task] [priority]` - Add a task with a certain priority from 1 to 3
                `/task list` - View all your tasks

                __Reminder Commands__
                `/reminder add [time] [message]` - Set a reminder for a certain time
                `/reminder list` - View all your reminders

                **Note:** You can use `/` to see all available commands.''',
            color=0xffffff
        ),
        ephemeral=True
    )

# {interaction.user.mention} @mention

@bot.tree.command(name="task_add", description="Add a task to your task list")
@app_commands.describe(task="The task you want to add", priority="The priority of the task")
async def task_add(interaction: discord.Interaction, task: str, priority: str):
    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"Task `{task}` with priority '{priority}' added to your todo list.",
            color=0xffffff
        ),
        ephemeral=True
    )

@bot.tree.command(name="task_list", description="View all your tasks")
async def task_list(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=discord.Embed(
            description=f"Here are your tasks:\n1. Task 1\n2. Task 2\n3. Task 3",
            color=0xffffff
        ),
        ephemeral=True
    )

bot.run(TOKEN)
