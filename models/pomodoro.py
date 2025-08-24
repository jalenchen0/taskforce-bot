from enum import Enum
import asyncio

class PomodoroState(Enum):
    IDLE = 0
    WORKING = 1
    SHORT_BREAK = 2
    LONG_BREAK = 3

class PomodoroSession:
    def __init__(self, user_id, work_duration=25, break_duration=5, long_break_duration=15, sessions_before_long_break=4):
        self.user_id = user_id
        self.work_duration = work_duration
        self.break_duration = break_duration
        self.long_break_duration = long_break_duration
        self.sessions_before_long_break = sessions_before_long_break
        self.state = PomodoroState.IDLE
        self.remaining_time = 0
        self.completed_sessions = 0
        self.task = None
        self.message = None

active_pomodoro_sessions = {}
