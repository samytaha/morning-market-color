"""OS-isolated clipboard copy. Never raises — returns False if unavailable."""
import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    try:
        if sys.platform == "win32":
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-16-le"))
            return proc.returncode == 0
        if sys.platform == "darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-8"))
            return proc.returncode == 0
    except Exception:
        return False
    return False
