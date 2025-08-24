import discord
from discord import app_commands
from discord.ext import commands
from models.database import Database
from utils.views import DeletableDropdown

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
            await Database.add_task(
                interaction.user.id,
                self.task.value,
                int(self.priority.value)
            )
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

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    task = app_commands.Group(name="task", description="Manage your tasks")

    @task.command(name="add", description="Add a new task")
    async def task_add(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TaskModal())

    @task.command(name="list", description="View your tasks")
    async def task_list(self, interaction: discord.Interaction):
        try:
            tasks = await Database.get_tasks(interaction.user.id)
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

async def setup(bot):
    await bot.add_cog(Tasks(bot))
