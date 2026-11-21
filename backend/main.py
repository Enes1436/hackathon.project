import tkinter as tk
from dashboard import Dashboard
from config import APP_NAME

def main():
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1200x760")
    root.minsize(900, 600)
    Dashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()