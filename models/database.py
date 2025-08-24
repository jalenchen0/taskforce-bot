import json
import httpx
from config import SUPABASE_URL, HEADERS

class Database:
    @staticmethod
    async def execute_query(endpoint, method="GET", json_data=None):
        async with httpx.AsyncClient() as client:
            try:
                method = method.lower()
                if method == "get":
                    response = await client.get(f"{SUPABASE_URL}/{endpoint}", headers=HEADERS)
                elif method == "post":
                    response = await client.post(f"{SUPABASE_URL}/{endpoint}", headers=HEADERS, json=json_data)
                elif method == "delete":
                    response = await client.delete(f"{SUPABASE_URL}/{endpoint}", headers=HEADERS)
                elif method == "patch":
                    response = await client.patch(f"{SUPABASE_URL}/{endpoint}", headers=HEADERS, json=json_data)

                if response.status_code == 204:
                    return None
                elif response.content:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return response.text
                else:
                    return None

            except httpx.HTTPError as e:
                print(f"HTTP error: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error in execute_query: {e}")
                return None

    @staticmethod
    async def get_user_timezone(user_id):
        try:
            data = await Database.execute_query(f"rest/v1/timezones?user_id=eq.{user_id}")
            return data[0]["utc_offset"] if data else 0
        except:
            return 0

    @staticmethod
    async def set_user_timezone(user_id, offset):
        await Database.execute_query(
            "rest/v1/timezones",
            method="POST",
            json_data={"user_id": user_id, "utc_offset": offset}
        )

    @staticmethod
    async def get_tasks(user_id):
        return await Database.execute_query(f"rest/v1/tasks?user_id=eq.{user_id}")

    @staticmethod
    async def add_task(user_id, task, priority):
        await Database.execute_query(
            "rest/v1/tasks",
            method="POST",
            json_data={"user_id": user_id, "task": task, "priority": priority}
        )

    @staticmethod
    async def delete_task(task_id):
        await Database.execute_query(f"rest/v1/tasks?id=eq.{task_id}", method="DELETE")

    @staticmethod
    async def get_reminders(user_id):
        return await Database.execute_query(f"rest/v1/reminders?user_id=eq.{user_id}")

    @staticmethod
    async def add_reminder(user_id, message, remind_at):
        await Database.execute_query(
            "rest/v1/reminders",
            method="POST",
            json_data={"user_id": user_id, "message": message, "remind_at": remind_at}
        )

    @staticmethod
    async def delete_reminder(reminder_id):
        await Database.execute_query(f"rest/v1/reminders?id=eq.{reminder_id}", method="DELETE")

    @staticmethod
    async def get_due_reminders(start_time, end_time):
        return await Database.execute_query(
            f"rest/v1/reminders?remind_at=gt.{start_time}&remind_at=lte.{end_time}"
        )

    @staticmethod
    async def get_pomodoro_settings(user_id):
        try:
            data = await Database.execute_query(f"rest/v1/pomodoro_sessions?user_id=eq.{user_id}")
            return data[0] if data else None
        except:
            return None

    @staticmethod
    async def save_pomodoro_settings(user_id, work_duration, break_duration, long_break_duration, sessions_before_long_break):
        await Database.execute_query(
            "rest/v1/pomodoro_sessions",
            method="POST",
            json_data={
                "user_id": user_id,
                "work_duration": work_duration,
                "break_duration": break_duration,
                "long_break_duration": long_break_duration,
                "sessions_before_long_break": sessions_before_long_break
            }
        )
