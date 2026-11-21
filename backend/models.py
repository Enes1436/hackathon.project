from dataclasses import dataclass

@dataclass(slots=True)
class Note:
    title: str
    content: str

@dataclass(slots=True)
class Task:
    title: str
    done: bool = False

@dataclass(slots=True)
class QuizQuestion:
    question: str
    options: tuple[str, ...]
    answer: int