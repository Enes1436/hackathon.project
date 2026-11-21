from pathlib import Path
import json

def export_text(path, rows):
    text = "\n\n".join(f"{role.upper()}\n{content}" for role, content in rows)
    Path(path).write_text(text, encoding="utf-8")

def export_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )