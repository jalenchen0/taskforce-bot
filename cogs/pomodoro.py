import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from models.database import Database
from models.pomodoro import PomodoroSession, PomodoroState, active_pomodoro_sessions
from utils.helpers import format_remaining_time, create_progress_bar

class PomodoroSettingsModal(discord.ui.Modal, title='Pomodoro Settings'):
    work_duration = discord.ui.TextInput(
        label='Work Duration (minutes)',
        placeholder='25',
        default='25',
        required=True,
        max_length=3
    )

    break_duration = discord.ui.TextInput(
        label='Short Break (minutes)',
        placeholder='5',
        default='5',
        required=True,
        max_length=3
    )

    long_break_duration = discord.ui.TextInput(
        label='Long Break (minutes)',
        placeholder='15',
        default='15',
        required=True,
        max_length=3
    )

    sessions_before_long_break = discord.ui.TextInput(
        label='Sessions Before Long Break',
        placeholder='4',
        default='4',
        required=True,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            work = int(self.work_duration.value)
            break_dur = int(self.break_duration.value)
            long_break = int(self.long_break_duration.value)
            sessions = int(self.sessions_before_long_break.value)

            if work < 1 or break_dur < 1 or long_break < 1 or sessions < 1:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Invalid Values",
                        description="All values must be at least 1",
                        color=0xff0000
                    ),
                    ephemeral=True
                )

            await Database.save_pomodoro_settings(
                interaction.user.id,
                work,
                break_dur,
                long_break,
                sessions
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Pomodoro Settings Saved",
                    description=f"Work: {work} min, Break: {break_dur} min, Long Break: {long_break} min, Sessions: {sessions}",
                    color=0x00ff00
                ),
                ephemeral=True
            )

        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Input",
                    description="Please enter valid numbers",
                    color=0xff0000
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error Saving Settings",
                    description=f"Failed to save settings: {e}",
                    color=0xff0000
                ),
                ephemeral=True
            )

async def update_pomodoro_message(session, minutes, seconds):
    if session.state == PomodoroState.WORKING:
        total_duration = session.work_duration * 60
        title = "🍅 Pomodoro Session"
        emoji = "🔴"
    elif session.state == PomodoroState.SHORT_BREAK:
        total_duration = session.break_duration * 60
        title = "☕ Short Break"
        emoji = "🟢"
    else:
        total_duration = session.long_break_duration * 60
        title = "🌴 Long Break"
        emoji = "🟢"

    progress = 1 - (session.remaining_time / total_duration)
    progress_bar = create_progress_bar(progress)

    embed = discord.Embed(
        title=title,
        description=f"{emoji} **{minutes:02d}:{seconds:02d}** remaining\n{progress_bar}",
        color=0xffffff if session.state == PomodoroState.WORKING else 0x00ff00
    ).add_field(
        name="Completed Sessions",
        value=f"{session.completed_sessions}/{session.sessions_before_long_break}",
        inline=True
    ).set_footer(text="Type /pomodoro stop to end your session")

    if session.message:
        try:
            await session.message.edit(embed=embed)
        except:
            session.message = await session.bot.get_user(session.user_id).send(embed=embed)
    else:
        session.message = await session.bot.get_user(session.user_id).send(embed=embed)

async def pomodoro_timer(session):
    while session.state != PomodoroState.IDLE and session.remaining_time > 0:
        minutes = session.remaining_time // 60
        seconds = session.remaining_time % 60

        if session.remaining_time % 5 == 0:
            await update_pomodoro_message(session, minutes, seconds)

        await asyncio.sleep(1)
        session.remaining_time -= 1

    if session.state != PomodoroState.IDLE:
        if session.state == PomodoroState.WORKING:
            session.completed_sessions += 1
            embed = discord.Embed(
                title="✅ Work Session Complete!",
                description="Time for a break!",
                color=0x00ff00
            )

            if session.completed_sessions >= session.sessions_before_long_break:
                session.state = PomodoroState.LONG_BREAK
                session.remaining_time = session.long_break_duration * 60
                embed.add_field(
                    name="Next",
                    value=f"Long break: {session.long_break_duration} minutes",
                    inline=False
                )
            else:
                session.state = PomodoroState.SHORT_BREAK
                session.remaining_time = session.break_duration * 60
                embed.add_field(
                    name="Next",
                    value=f"Short break: {session.break_duration} minutes",
                    inline=False
                )

            await session.bot.get_user(session.user_id).send(embed=embed)

        else:
            session.state = PomodoroState.WORKING
            session.remaining_time = session.work_duration * 60

            embed = discord.Embed(
                title="🔔 Break Time Over!",
                description="Time to get back to work!",
                color=0xff9900
            )
            embed.add_field(
                name="Next",
                value=f"Work session: {session.work_duration} minutes",
                inline=False
            )

            await session.bot.get_user(session.user_id).send(embed=embed)

        session.task = asyncio.create_task(pomodoro_timer(session))

class Pomodoro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    pomodoro = app_commands.Group(name="pomodoro", description="Pomodoro timer commands")

    @pomodoro.command(name="start", description="Start a Pomodoro session")
    async def pomodoro_start(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in active_pomodoro_sessions:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Session Already Active",
                    description="You already have an active Pomodoro session. Use `/pomodoro stop` to end it first.",
                    color=0xff0000
                ),
                ephemeral=True
            )

        settings = await Database.get_pomodoro_settings(user_id)
        if not settings:
            settings = {
                "work_duration": 25,
                "break_duration": 5,
                "long_break_duration": 15,
                "sessions_before_long_break": 4
            }

        session = PomodoroSession(
            user_id=user_id,
            work_duration=settings["work_duration"],
            break_duration=settings["break_duration"],
            long_break_duration=settings["long_break_duration"],
            sessions_before_long_break=settings["sessions_before_long_break"]
        )
        session.bot = self.bot

        session.state = PomodoroState.WORKING
        session.remaining_time = session.work_duration * 60
        session.task = asyncio.create_task(pomodoro_timer(session))

        active_pomodoro_sessions[user_id] = session

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🍅 Pomodoro Started",
                description=f"Work session started for {session.work_duration} minutes!",
                color=0xffffff
            ),
            ephemeral=True
        )

    @pomodoro.command(name="stop", description="Stop your current Pomodoro session")
    async def pomodoro_stop(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id not in active_pomodoro_sessions:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ No Active Session",
                    description="You don't have an active Pomodoro session.",
                    color=0xff0000
                ),
                ephemeral=True
            )

        session = active_pomodoro_sessions[user_id]
        session.state = PomodoroState.IDLE

        if session.task:
            session.task.cancel()

        del active_pomodoro_sessions[user_id]

        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏹️ Pomodoro Stopped",
                description="Your Pomodoro session has been stopped.",
                color=0xffffff
            ),
            ephemeral=True
        )

    @pomodoro.command(name="settings", description="Configure your Pomodoro timer settings")
    async def pomodoro_settings(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PomodoroSettingsModal())

    @pomodoro.command(name="status", description="Check your current Pomodoro session status")
    async def pomodoro_status(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id not in active_pomodoro_sessions:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ No Active Session",
                    description="You don't have an active Pomodoro session.",
                    color=0xff0000
                ),
                ephemeral=True
            )

        session = active_pomodoro_sessions[user_id]

        minutes = session.remaining_time // 60
        seconds = session.remaining_time % 60

        if session.state == PomodoroState.WORKING:
            state_str = "Work Session"
            emoji = "🔴"
        elif session.state == PomodoroState.SHORT_BREAK:
            state_str = "Short Break"
            emoji = "🟢"
        else:
            state_str = "Long Break"
            emoji = "🟢"

        embed = discord.Embed(
            title=f"{emoji} Pomodoro Status",
            description=f"**{state_str}**: {minutes:02d}:{seconds:02d} remaining",
            color=0xffffff
        )

        embed.add_field(
            name="Completed Sessions",
            value=f"{session.completed_sessions}/{session.sessions_before_long_break}",
            inline=True
        )

        embed.add_field(
            name="Next Session",
            value="Long Break" if session.completed_sessions + 1 >= session.sessions_before_long_break else "Short Break",
            inline=True
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    def cog_unload(self):
        for user_id, session in active_pomodoro_sessions.items():
            if session.task:
                session.task.cancel()
        active_pomodoro_sessions.clear()

async def setup(bot):
    await bot.add_cog(Pomodoro(bot))
