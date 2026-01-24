#!/usr/bin/env python3
"""Taximate - Tax calculation assistant."""

import tkinter as tk

from src.gui import TaximateGUI


def main() -> None:
    root = tk.Tk()
    app = TaximateGUI(root)
    app.run()


if __name__ == "__main__":
    main()
