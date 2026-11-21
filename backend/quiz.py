import random
from models import QuizQuestion

QUESTIONS = [
    QuizQuestion("Which keyword defines a function?", ("function", "def", "func", "define"), 1),
    QuizQuestion("Which type stores key-value pairs?", ("list", "tuple", "dict", "set"), 2),
    QuizQuestion("Which extension is used for Python?", (".java", ".py", ".cpp", ".html"), 1),
    QuizQuestion("What does len() return?", ("Length", "A file", "A loop", "A class"), 0),
]

def get_quiz():
    questions = QUESTIONS.copy()
    random.shuffle(questions)
    return questions