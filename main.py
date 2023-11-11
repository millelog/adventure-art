import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import tkinter as tk
from gui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

