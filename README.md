# Taskforce Bot

A personal task force. A Discord utility and productivity bot that you can use to capture your tasks and reminders. For people who check Discord but forget to check their to-do list and reminders. Includes a pomodoro timer feature.

You can set priorities from 1 to 3 for your tasks from high to low priority.

For reminders, you put the date in `YYYY-MM-DD` format and the time in 24-hour `HH:MM` format. Include a 0 in the front for single digit numbers. Times are adjusted to the timezone you set. 
A reminder will be sent to you through DMs on the date and time indicated with the message provided.

# /help
__General Commands__ <br>
`/help` - Shows this message <br>
`/set_timezone [UTC offset]` - Set your timezone offset from UTC (e.g. -5, 0, 2). It is set to 0 by default. <br>

__Task Commands__ <br>
`/task add` - Add a new task. Prompts you to fill out a form. Input a certain priority from 1 to 3, from high to low priority, along with a message. <br>
`/task list` - View all your tasks <br>

__Reminder Commands__ <br>
`/reminder add` - Set a new reminder. Prompts you to full out a form. Input a date, a time, and a message. <br>
`/reminder list` - View all your reminders <br>

__Pomodoro Commands__ <br>
`/pomodoro start` - Start a Pomodoro session <br>
`/pomodoro stop` - Stop your current Pomodoro session <br>
`/pomodoro status` - View the status of your current Pomodoro session <br>
`/pomodoro settings` - View or change your Pomodoro settings <br>
