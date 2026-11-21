import json
import urllib.request
import urllib.error
from config import load_config

SYSTEM_PROMPT = """You are SmartDesk AI, a helpful educational assistant.
Answer clearly and accurately. When programming is involved, prefer modern,
safe and runnable Python examples. Answer in the user's language when possible."""

class AIAssistant:
    def __init__(self):
        self.config = load_config()

    def ask(self, prompt, history=None):
        api_key = self.config.get("api_key", "").strip()
        if not api_key:
            return "API Key nuk është vendosur. Hape Settings dhe vendose API Key."

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": self.config.get("model", "gpt-4.1-mini"),
            "messages": messages,
            "temperature": 0.6
        }).encode("utf-8")

        request = urllib.request.Request(
            self.config.get("api_endpoint"),
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"Unexpected API response: {exc}"
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            return f"API error {exc.code}: {detail}"
        except Exception as exc:
            return f"Connection error: {exc}"