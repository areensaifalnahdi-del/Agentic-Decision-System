from datetime import datetime


def log_message(sender, receiver, message):
    timestamp = datetime.now().strftime("%H:%M:%S")

    with open("communication_log.txt", "a") as file:
        file.write(
            f"{timestamp} {sender} -> {receiver}: {message}\n"
        )