SmartDesk 3.15

This project has separate web frontend and backend folders:

- `frontend/` contains HTML, CSS, and JavaScript.
- `backend/` contains the Python HTTP API server.
- The existing Python modules provide the database and application logic.

Start the web application:

```powershell
py -3 backend/server.py
```

Open `http://127.0.0.1:8000`.

The original Tkinter desktop entry point remains available with `py -3 backend/main.py`.
Copy `backend/config_example.json` to `backend/config.json` and add an API key only if you want AI chat.