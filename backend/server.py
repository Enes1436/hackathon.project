import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from ai_assistant import AIAssistant
from calculator import calculate
from code_runner import run_python_code
from config import load_config, save_config
from database import Database
from quiz import get_quiz
from statistics import StatisticsService


database = Database()
assistant = AIAssistant()


class Handler(BaseHTTPRequestHandler):
    server_version = "SmartDeskServer/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                return None
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return None

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith("/api/"):
            self.handle_api_get(path)
            return

        if path in ("", "/"):
            path = "/index.html"
        requested = (FRONTEND / path.lstrip("/")).resolve()
        try:
            requested.relative_to(FRONTEND.resolve())
        except ValueError:
            self.send_error(403)
            return
        if not requested.is_file():
            self.send_error(404)
            return
        content = requested.read_bytes()
        content_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_api_get(self, path):
        if path == "/api/dashboard":
            self.send_json(200, StatisticsService(database).get())
        elif path == "/api/notes":
            self.send_json(200, [
                {"id": row[0], "title": row[1], "content": row[2]}
                for row in database.get_notes()
            ])
        elif path == "/api/tasks":
            self.send_json(200, [
                {"id": row[0], "title": row[1], "done": bool(row[2])}
                for row in database.get_tasks()
            ])
        elif path == "/api/chat":
            self.send_json(200, [
                {"role": role, "content": content}
                for role, content in database.get_chat()
            ])
        elif path == "/api/quiz":
            self.send_json(200, [
                {"question": item.question, "options": list(item.options), "answer": item.answer}
                for item in get_quiz()
            ])
        elif path == "/api/settings":
            config = load_config()
            self.send_json(200, {
                "theme": config.get("theme", "dark"),
                "api_endpoint": config.get("api_endpoint", ""),
                "model": config.get("model", ""),
                "api_key": config.get("api_key", ""),
                "ai_configured": bool(config.get("api_key", "").strip())
            })
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        data = self.read_json()
        if data is None:
            self.send_json(400, {"error": "Invalid JSON"})
            return

        if path == "/api/notes":
            title = str(data.get("title", "")).strip()
            content = str(data.get("content", "")).strip()
            if not title or not content:
                self.send_json(400, {"error": "Title and content are required"})
                return
            database.add_note(title[:200], content[:50000])
            self.send_json(201, {"ok": True})
        elif path == "/api/tasks":
            title = str(data.get("title", "")).strip()
            if not title:
                self.send_json(400, {"error": "Task title is required"})
                return
            database.add_task(title[:500])
            self.send_json(201, {"ok": True})
        elif path == "/api/chat":
            prompt = str(data.get("prompt", "")).strip()
            if not prompt:
                self.send_json(400, {"error": "Prompt is required"})
                return
            config = load_config()
            if not config.get("api_key", "").strip():
                self.send_json(200, {
                    "answer": "AI setup required. Add an API key in Settings first.",
                    "requires_api_key": True
                })
                return
            old_history = database.get_chat()
            database.add_chat("user", prompt[:5000])
            answer = assistant.ask(prompt[:5000], [
                {"role": role, "content": content}
                for role, content in old_history
            ])
            database.add_chat("assistant", answer)
            self.send_json(200, {
                "answer": answer,
                "requires_api_key": not bool(assistant.config.get("api_key", "").strip())
            })
        elif path == "/api/code":
            code = str(data.get("code", ""))
            if len(code) > 50000:
                self.send_json(400, {"error": "Code is too large"})
                return
            self.send_json(200, {"output": run_python_code(code)})
        elif path == "/api/calculate":
            expression = str(data.get("expression", ""))
            try:
                result = calculate(expression)
                self.send_json(200, {"result": result})
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})
        elif path == "/api/settings":
            config = load_config()
            for key in ("theme", "api_endpoint", "model", "api_key"):
                if key in data:
                    config[key] = str(data[key]).strip()
            save_config(config)
            assistant.config = config
            self.send_json(200, {"ok": True})
        elif path == "/api/chat/clear":
            database.clear_chat()
            self.send_json(200, {"ok": True})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_PUT(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith("/api/tasks/"):
            try:
                task_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                self.send_json(400, {"error": "Invalid task ID"})
                return
            database.toggle_task(task_id)
            self.send_json(200, {"ok": True})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith("/api/notes/"):
            try:
                database.delete_note(int(path.rsplit("/", 1)[1]))
                self.send_json(200, {"ok": True})
            except ValueError:
                self.send_json(400, {"error": "Invalid note ID"})
        elif path.startswith("/api/tasks/"):
            try:
                database.delete_task(int(path.rsplit("/", 1)[1]))
                self.send_json(200, {"ok": True})
            except ValueError:
                self.send_json(400, {"error": "Invalid task ID"})
        else:
            self.send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


def main():
    host = "127.0.0.1"
    port = 8000
    print(f"SmartDesk running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
