import subprocess
import sys
import tempfile
from pathlib import Path

def run_python_code(code, timeout=8):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "program.py"
        path.write_text(code, encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += ("\n" if output else "") + result.stderr
            return output.strip() or f"Exit code: {result.returncode}"
        except subprocess.TimeoutExpired:
            return "Program stopped: time limit reached."
        except Exception as exc:
            return f"Unable to run program: {exc}"