"""Entry point for the Musical Gesture Recognition application."""

import tkinter as tk
from app import MusicalGestureApp


def main():
    """Run the application."""
    root = tk.Tk()

    # Set initial window size
    root.geometry("1000x600")

    # Create and run the application
    app = MusicalGestureApp(root)
    app.root.mainloop()


if __name__ == "__main__":
    main()