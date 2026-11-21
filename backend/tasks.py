class TaskService:
    def __init__(self, database):
        self.database = database

    def add(self, title):
        if title.strip():
            self.database.add_task(title.strip())