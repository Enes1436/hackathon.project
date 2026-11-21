import tkinter as tk
from tkinter import ttk, messagebox
import threading

from config import load_config, save_config
from database import Database
from ai_assistant import AIAssistant
from code_runner import run_python_code
from calculator import calculate
from statistics import StatisticsService
from theme import get_theme

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.database = Database()
        self.ai = AIAssistant()
        self.history = self.database.get_chat()
        self.chat_busy = False
        self.chat_view = None
        self.nav_buttons = {}
        self.theme = get_theme(self.config.get("theme", "dark"))
        self.apply_theme()
        self.build()
        self.show_dashboard()

    def apply_theme(self):
        self.root.configure(bg=self.theme["bg"])
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=self.theme["bg"], foreground=self.theme["fg"],
                        font=("Segoe UI", 10))
        style.configure("Card.TFrame", background=self.theme["panel"])
        style.configure("Content.TFrame", background=self.theme["bg"])
        style.configure("Sidebar.TFrame", background=self.theme["panel"])
        style.configure("Title.TLabel", background=self.theme["bg"],
                        foreground=self.theme["fg"], font=("Segoe UI", 20, "bold"))
        style.configure("CardTitle.TLabel", background=self.theme["panel"],
                        foreground=self.theme["fg"], font=("Segoe UI", 13, "bold"))
        style.configure("Muted.TLabel", background=self.theme["panel"],
                        foreground="#9ca3af")
        style.configure("Nav.TButton", padding=(12, 9), anchor="w")
        style.configure("Primary.TButton", padding=(12, 8))
        style.configure("TEntry", fieldbackground=self.theme["panel"],
                        foreground=self.theme["fg"], insertcolor=self.theme["fg"])
        style.configure("TNotebook", background=self.theme["bg"],
                        borderwidth=0)

    def build(self):
        top = ttk.Frame(self.root, padding=(18, 12), style="Card.TFrame")
        top.pack(fill="x", side="top")
        ttk.Label(top, text="SMARTDESK", style="CardTitle.TLabel",
                  font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(top, text="3.15", style="Muted.TLabel").pack(side="left", padx=(5, 0))
        ttk.Button(top, text="Settings", style="Primary.TButton",
                   command=self.settings).pack(side="right")

        body = ttk.Frame(self.root, style="Content.TFrame")
        body.pack(fill="both", expand=True)

        sidebar = ttk.Frame(body, width=190, padding=12, style="Sidebar.TFrame")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("AI Assistant", self.show_chat),
            ("Python Code Lab", self.show_code),
            ("Calculator", self.show_calculator),
            ("Notes", self.show_notes),
            ("Tasks", self.show_tasks),
            ("Quiz", self.show_quiz),
            ("Statistics", self.show_statistics),
        ]
        for name, command in nav_items:
            button = ttk.Button(sidebar, text=name, style="Nav.TButton", command=command)
            button.pack(fill="x", pady=3)
            self.nav_buttons[name] = button

        self.content = ttk.Frame(body, padding=22, style="Content.TFrame")
        self.content.pack(side="left", fill="both", expand=True)

    def clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def title(self, text):
        ttk.Label(self.content, text=text, style="Title.TLabel").pack(
            anchor="w", pady=(0, 16))

    def show_dashboard(self):
        self.clear()
        self.title("Dashboard")
        stats = StatisticsService(self.database).get()
        cards = ttk.Frame(self.content, style="Content.TFrame")
        cards.pack(fill="x")
        card_data = [
            ("NOTES", stats["notes"]),
            ("TASKS", stats["tasks"]),
            ("COMPLETED", stats["completed"]),
            ("AI MESSAGES", stats["messages"]),
        ]
        for label, value in card_data:
            card = ttk.Frame(cards, padding=18, style="Card.TFrame")
            card.pack(side="left", fill="x", expand=True, padx=(0, 10))
            ttk.Label(card, text=str(value), style="CardTitle.TLabel",
                      font=("Segoe UI", 22, "bold")).pack(anchor="w")
            ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(
            self.content,
            text="AI assistance, Python tools, notes, tasks, and study in one focused workspace.",
            font=("Segoe UI", 12),
            background=self.theme["bg"], foreground=self.theme["fg"]
        ).pack(anchor="w", pady=24)

    def show_chat(self):
        self.clear()
        self.title("AI Assistant")
        chat = tk.Text(
            self.content, wrap="word", state="disabled", relief="flat",
            padx=14, pady=14, font=("Segoe UI", 11),
            bg=self.theme["panel"], fg=self.theme["fg"],
            insertbackground=self.theme["fg"]
        )
        chat.pack(fill="both", expand=True)
        self.chat_view = chat

        for role, content in self.history:
            chat.insert("end", f"{role.upper()}\n{content}\n\n")
        chat.config(state="disabled")
        chat.see("end")

        row = ttk.Frame(self.content)
        row.pack(fill="x", pady=8)
        entry = ttk.Entry(row)
        entry.pack(side="left", fill="x", expand=True)
        status = ttk.Label(row, text="Ready")
        status.pack(side="right", padx=8)
        send_button = ttk.Button(row, text="Send")
        send_button.pack(side="right")

        def send():
            if self.chat_busy:
                return
            prompt = entry.get().strip()
            if not prompt:
                return

            self.chat_busy = True
            send_button.config(state="disabled")
            entry.config(state="disabled")
            entry.delete(0, "end")
            old_history = self.database.get_chat()
            self.database.add_chat("user", prompt)
            self.history = self.database.get_chat()

            if chat.winfo_exists():
                chat.config(state="normal")
                chat.insert("end", f"USER\n{prompt}\n\n")
                chat.config(state="disabled")
                chat.see("end")
            status.config(text="Thinking...")

            def work():
                try:
                    answer = self.ai.ask(prompt, [
                        {"role": r, "content": c} for r, c in old_history
                    ])
                except Exception as exc:
                    answer = f"Unexpected assistant error: {exc}"
                self.database.add_chat("assistant", answer)
                self.history = self.database.get_chat()
                self.root.after(
                    0,
                    lambda: self.finish_chat(chat, status, entry, send_button, answer)
                )

            threading.Thread(target=work, daemon=True).start()

        send_button.config(command=send)
        entry.bind("<Return>", lambda event: send())

    def finish_chat(self, chat, status, entry, send_button, answer):
        self.chat_busy = False
        if chat.winfo_exists():
            chat.config(state="normal")
            chat.insert("end", f"AI\n{answer}\n\n")
            chat.config(state="disabled")
            chat.see("end")
        if status.winfo_exists():
            status.config(text="Ready")
        if entry.winfo_exists():
            entry.config(state="normal")
            entry.focus_set()
        if send_button.winfo_exists():
            send_button.config(state="normal")

    def show_code(self):
        self.clear()
        self.title("Python Code Lab")

        editor = tk.Text(self.content, height=18, font=("Consolas", 11),
                         bg=self.theme["panel"], fg=self.theme["fg"],
                         insertbackground=self.theme["fg"], relief="flat",
                         padx=12, pady=12)
        editor.pack(fill="both", expand=True)
        editor.insert("1.0", 'print("Hello from SmartDesk!")')

        output = tk.Text(self.content, height=8, font=("Consolas", 10),
                         bg=self.theme["panel"], fg=self.theme["fg"],
                         relief="flat", padx=12, pady=12)
        output.pack(fill="x", pady=8)

        def run():
            output.delete("1.0", "end")
            output.insert("end", run_python_code(editor.get("1.0", "end")))

        ttk.Button(self.content, text="Run Python", command=run).pack()

    def show_calculator(self):
        self.clear()
        self.title("Safe Calculator")

        entry = ttk.Entry(self.content, font=("Segoe UI", 16))
        entry.pack(fill="x")
        result = ttk.Label(self.content, text="Result:", font=("Segoe UI", 13))
        result.pack(anchor="w", pady=10)

        def calculate_value():
            try:
                result.config(text=f"Result: {calculate(entry.get())}")
            except Exception as exc:
                result.config(text=f"Error: {exc}")

        ttk.Button(self.content, text="Calculate",
                   command=calculate_value).pack(anchor="w")

    def show_notes(self):
        self.clear()
        self.title("Notes")

        title = ttk.Entry(self.content)
        title.pack(fill="x", pady=(0, 6))
        content = tk.Text(self.content, height=5, font=("Segoe UI", 10),
                          bg=self.theme["panel"], fg=self.theme["fg"],
                          insertbackground=self.theme["fg"], relief="flat",
                          padx=10, pady=10)
        content.pack(fill="x")
        notes = tk.Listbox(self.content, height=10, bg=self.theme["panel"],
                           fg=self.theme["fg"], relief="flat",
                           selectbackground="#2563eb",
                           selectforeground="#ffffff", font=("Segoe UI", 10))
        notes.pack(fill="both", expand=True, pady=8)
        note_rows = []

        def refresh():
            notes.delete(0, "end")
            note_rows[:] = self.database.get_notes()
            for note in note_rows:
                preview = note[2].replace("\n", " ")
                if len(preview) > 80:
                    preview = preview[:77] + "..."
                notes.insert("end", f"{note[1]}  —  {preview}")

        def add():
            note_title = title.get().strip()
            note_content = content.get("1.0", "end").strip()
            if not note_title or not note_content:
                messagebox.showwarning("Missing content", "Enter both a title and note content.")
                return
            self.database.add_note(note_title, note_content)
            title.delete(0, "end")
            content.delete("1.0", "end")
            refresh()

        def delete_selected():
            selection = notes.curselection()
            if not selection:
                return
            note_id = note_rows[selection[0]][0]
            self.database.delete_note(note_id)
            refresh()

        actions = ttk.Frame(self.content)
        actions.pack(anchor="w")
        ttk.Button(actions, text="Add Note", command=add).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Delete Selected", command=delete_selected).pack(side="left")
        refresh()

    def show_tasks(self):
        self.clear()
        self.title("Tasks")

        entry = ttk.Entry(self.content)
        entry.pack(fill="x")
        tasks = tk.Listbox(self.content, bg=self.theme["panel"], fg=self.theme["fg"],
                           relief="flat", selectbackground="#2563eb",
                           selectforeground="#ffffff", font=("Segoe UI", 10))
        tasks.pack(fill="both", expand=True, pady=5)
        task_rows = []

        def refresh():
            tasks.delete(0, "end")
            task_rows[:] = self.database.get_tasks()
            for task in task_rows:
                mark = "✓" if task[2] else "○"
                tasks.insert("end", f"{task[0]}  {mark}  {task[1]}")

        def add():
            if entry.get().strip():
                self.database.add_task(entry.get())
                entry.delete(0, "end")
                refresh()

        def toggle():
            selection = tasks.curselection()
            if selection:
                task_id = task_rows[selection[0]][0]
                self.database.toggle_task(task_id)
                refresh()

        def delete_selected():
            selection = tasks.curselection()
            if not selection:
                return
            task_id = task_rows[selection[0]][0]
            self.database.delete_task(task_id)
            refresh()

        actions = ttk.Frame(self.content)
        actions.pack(anchor="w")
        ttk.Button(actions, text="Add", command=add).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Toggle", command=toggle).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Delete", command=delete_selected).pack(side="left")
        entry.bind("<Return>", lambda event: add())
        refresh()

    def show_quiz(self):
        from quiz import get_quiz
        self.clear()
        self.title("Python Quiz")

        questions = get_quiz()
        index = [0]
        score = [0]

        question = ttk.Label(self.content, text="", wraplength=800)
        question.pack(anchor="w", pady=15)

        answer = tk.IntVar(value=-1)
        radios = []
        for i in range(4):
            radio = ttk.Radiobutton(
                self.content, variable=answer, value=i, text=""
            )
            radio.pack(anchor="w", pady=3)
            radios.append(radio)

        def render():
            item = questions[index[0]]
            question.config(text=item.question)
            answer.set(-1)
            for i, radio in enumerate(radios):
                radio.config(text=item.options[i])

        def next_question():
            selected = answer.get()
            if selected == -1:
                messagebox.showwarning("Select an answer", "Choose one option before continuing.")
                return
            if selected == questions[index[0]].answer:
                score[0] += 1
            index[0] += 1

            if index[0] >= len(questions):
                messagebox.showinfo(
                    "Quiz Result",
                    f"Score: {score[0]}/{len(questions)}"
                )
                self.show_quiz()
            else:
                render()

        ttk.Button(self.content, text="Next",
                   command=next_question).pack(pady=15)
        render()

    def show_statistics(self):
        self.clear()
        self.title("Statistics")
        stats = StatisticsService(self.database).get()
        for key, value in stats.items():
            ttk.Label(
                self.content,
                text=f"{key.replace('_', ' ').title()}: {value}",
                font=("Segoe UI", 13)
            ).pack(anchor="w", pady=5)

    def settings(self):
        window = tk.Toplevel(self.root)
        window.title("SmartDesk Settings")
        window.geometry("620x320")
        window.configure(bg=self.theme["bg"])
        window.transient(self.root)

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        fields = {}
        for label, key in [
            ("API Key", "api_key"),
            ("API Endpoint", "api_endpoint"),
            ("Model", "model")
        ]:
            ttk.Label(frame, text=label).pack(anchor="w")
            entry = ttk.Entry(frame, show="*" if key == "api_key" else "")
            entry.pack(fill="x", pady=(3, 14))
            entry.insert(0, self.config.get(key, ""))
            fields[key] = entry

        ttk.Label(frame, text="Theme").pack(anchor="w")
        theme_value = tk.StringVar(
            value="dark" if self.config.get("theme", "dark") == "dark" else "light"
        )
        theme_select = ttk.Combobox(
            frame, textvariable=theme_value, values=("dark", "light"),
            state="readonly"
        )
        theme_select.pack(fill="x", pady=(3, 14))

        def save():
            for key, entry in fields.items():
                self.config[key] = entry.get().strip()
            self.config["theme"] = theme_value.get()
            save_config(self.config)
            self.ai.config = self.config
            self.theme = get_theme(self.config["theme"])
            self.apply_theme()
            window.destroy()
            self.show_dashboard()

        ttk.Button(frame, text="Save Settings",
                   command=save).pack(anchor="e")