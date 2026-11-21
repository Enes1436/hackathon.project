class StatisticsService:
    def __init__(self, database):
        self.database = database

    def get(self):
        tasks = self.database.get_tasks()
        return {
            "notes": len(self.database.get_notes()),
            "tasks": len(tasks),
            "completed": sum(task[2] for task in tasks),
            "messages": len(self.database.get_chat())
        }