class NotesService:
    def __init__(self, database):
        self.database = database

    def add(self, title, content):
        if not title.strip():
            raise ValueError("Title is required.")
        self.database.add_note(title.strip(), content.strip())