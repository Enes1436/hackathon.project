from pathlib import Path

SUPPORTED = {".py", ".txt", ".md", ".json", ".html", ".css", ".js", ".csv"}

def read_text(path, limit=50000):
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError("Unsupported text file.")
    return path.read_text(encoding="utf-8")[:limit]

def list_files(folder):
    return [p for p in Path(folder).iterdir() if p.is_file()]