import os
import subprocess
import sys
import threading
from typing import Callable, Dict, Optional


class ProcessRestarter:
    def __init__(self, python_executable: Optional[str] = None, main_script: str = 'main.py'):
        self.python_executable = python_executable or sys.executable
        self.main_script = main_script

    def build_restart_command(self) -> list[str]:
        return [self.python_executable, self.main_script]

    def restart(self) -> None:
        command = self.build_restart_command()
        subprocess.Popen(command, cwd=os.getcwd())

        def delayed_exit() -> None:
            os._exit(0)

        timer = threading.Timer(1.0, delayed_exit)
        timer.daemon = True
        timer.start()


class SystemControlService:
    def __init__(self, restarter: Optional[Callable[[], None]] = None):
        self.restarter = restarter or (lambda: None)

    def request_restart(self) -> Dict[str, str]:
        self.restarter()
        return {'status': 'scheduled'}
