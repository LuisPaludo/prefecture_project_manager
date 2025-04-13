from celery import shared_task
import datetime

@shared_task(name='prefecture_project_manager.tasks.print_console_message')
def print_console_message():
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"Hello! Task executed at {current_time}")
    return "Task completed"