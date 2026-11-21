DARK = {"bg": "#0b1020", "panel": "#111827", "fg": "#e5e7eb"}
LIGHT = {"bg": "#f3f4f6", "panel": "#ffffff", "fg": "#111827"}

def get_theme(name):
    return DARK if name == "dark" else LIGHT