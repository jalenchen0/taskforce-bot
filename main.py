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
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(f'''
        ## Taskforce Guide\n
        __General Commands:__\n
        /help - Shows this message\n
        \n
        __To-do Commands:__\n
        /todo add [task] [priority] - Add a task with a certain priority from 1-3\n
        /todo list - \nNote: You can use / to see all available commands.
    ''', ephemeral=True)

@bot.tree.command(name="todo_add", description="Add a task to your todo list")
@app_commands.describe(task="The task you want to add", priority="The priority of the task")
async def todo_add(interaction: discord.Interaction, task: str, priority: str):
    await interaction.response.send_message(f"{interaction.user.mention}: task '{task}' with priority '{priority}' added to your todo list.")

@bot.tree.command(name="todo_list", description="List all your tasks")
async def todo_list(interaction: discord.Interaction):
    await interaction.response.send_message(f"{interaction.user.mention}: Here are your tasks:\n1. Task 1\n2. Task 2\n3. Task 3")

bot.run(TOKEN)
