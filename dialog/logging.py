from datetime import datetime
from pathlib import Path


LOG_DIR = Path("dialog/logs")
LOG_DIR.mkdir(exist_ok=True)


def start_log():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"dialog_{timestamp}.txt"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Conversation started: {datetime.now()}\n")
        f.write("=" * 60 + "\n")

    return log_file


def log_user(log_file, text, dialog_act=None, state=None):
    with open(log_file, "a", encoding="utf-8") as f:
        if dialog_act and state:
            f.write(
                f"USER [{dialog_act} | {state}]: {text}\n"
            )
        else:
            f.write(f"USER: {text}\n")


def log_system(log_file, text, state=None):
    with open(log_file, "a", encoding="utf-8") as f:
        if state:
            f.write(f"SYSTEM [{state}]: {text}\n")
        else:
            f.write(f"SYSTEM: {text}\n")


def end_log(log_file):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"Conversation ended: {datetime.now()}\n")