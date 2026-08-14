"""Environment information without platform-specific assumptions."""

import os

from core.runtime import detect_runtime


class Environment:
    def info(self):
        runtime = detect_runtime()
        return {
            "platform": runtime.system,
            "platform_family": runtime.family,
            "release": runtime.release,
            "machine": runtime.machine,
            "python": runtime.python,
            "cwd": os.getcwd(),
            "termux": runtime.is_termux,
            "wsl": runtime.is_wsl,
        }
