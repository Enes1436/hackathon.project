import sqlite3
from config import DB_FILE

class Database:
    def __init__(self):
        self.initialize()

    def connect(self):
        return sqlite3.connect(str(DB_FILE))

    def initialize(self):
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS chat(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )""")

    def add_note(self, title, content):
        with self.connect() as db:
            db.execute("INSERT INTO notes(title,content) VALUES(?,?)", (title, content))

    def get_notes(self):
        with self.connect() as db:
            return db.execute("SELECT id,title,content FROM notes ORDER BY id DESC").fetchall()

    def delete_note(self, note_id):
        with self.connect() as db:
            db.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def add_task(self, title):
        with self.connect() as db:
            db.execute("INSERT INTO tasks(title) VALUES(?)", (title,))

    def get_tasks(self):
        with self.connect() as db:
            return db.execute("SELECT id,title,done FROM tasks ORDER BY id DESC").fetchall()

    def toggle_task(self, task_id):
        with self.connect() as db:
            db.execute("UPDATE tasks SET done = 1-done WHERE id=?", (task_id,))

    def delete_task(self, task_id):
        with self.connect() as db:
            db.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def add_chat(self, role, content):
        with self.connect() as db:
            db.execute("INSERT INTO chat(role,content) VALUES(?,?)", (role, content))

    def get_chat(self):
        with self.connect() as db:
            return db.execute("SELECT role,content FROM chat ORDER BY id").fetchall()

    def clear_chat(self):
        with self.connect() as db:
            db.execute("DELETE FROM chat")