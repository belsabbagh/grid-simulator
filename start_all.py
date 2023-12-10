import subprocess
import threading
import time
from src.gui import backend as be_gui
WAIT = 3

class NamedPopen(subprocess.Popen):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = name

def update_logger(textview, p: subprocess.Popen):
    while p.poll() is None:
        if p.stdout is None:
            continue
        line: bytes = p.stdout.readline()
        if not line:
            continue
        textview.log(line.decode("utf-8"))


if __name__ == "__main__":
    app = be_gui.BackendApp()
    processes: list[str] = [
        "ui.py",
        "server.py",
        "clients.py",
    ]
    loggers: dict[str, be_gui.TextView] = {
        "ui.py": app.main_window.ui_log,
        "server.py": app.main_window.server_log,
        "clients.py": app.main_window.clients_log,
    }
    subprocesses: list[NamedPopen] = []
    for p in processes:
        subprocesses.append(NamedPopen(p, ["python", f"src/gui/backend/{p}"]))
        time.sleep(WAIT)

    for p in subprocesses:
        name: str = p.name
        textview: be_gui.TextView = loggers[name]
        threading.Thread(target=update_logger, args=(textview, p)).start()
    print("All scripts started")
    app.exec()
