from datetime import datetime
from pathlib import Path
import re


LOG_DIR = Path("dialog/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def start_log(user_name, reasoning_transparency):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize the user's name to make it safe for filenames.
    safe_name = re.sub(r"[^\w-]", "_", user_name.strip())
    safe_name = safe_name or "user"

    transparency_label = (
        "ON" if reasoning_transparency else "OFF"
    )

    filename = (
        f"dialog_{safe_name}_transparency_{transparency_label}_"
        f"{timestamp}.txt"
    )

    log_file = LOG_DIR / filename

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Conversation started: {datetime.now()}\n")
        f.write(f"User: {user_name}\n")
        f.write(
            f"Reasoning transparency: {transparency_label}\n"
        )
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