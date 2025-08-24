import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import Intents

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=Intents.all())

async def load_cogs():
    await bot.load_extension("cogs.general")
    await bot.load_extension("cogs.tasks")
    await bot.load_extension("cogs.reminders")
    await bot.load_extension("cogs.pomodoro")

@bot.event
async def on_ready():
    print(f"Bot is ready: {bot.user.name} ({bot.user.id})")
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

bot.run(os.getenv('DISCORD_TOKEN'))
