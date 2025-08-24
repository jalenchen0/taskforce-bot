import discord
from discord.ui import View, Select
from models.database import Database

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
                if self.is_task:
                    await Database.delete_task(target_id)
                else:
                    await Database.delete_reminder(target_id)
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
