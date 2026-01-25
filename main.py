#!/usr/bin/env python3
"""Taximate - Self-employment tax calculation application.

This is the main entry point for the Taximate GUI application. It creates
the root Tkinter window with optional drag-and-drop support (via tkinterdnd2)
and launches the main GUI.

Usage:
    python main.py
    # or
    make run
"""

import contextlib
import tkinter as tk

from src.gui import TaximateGUI


def _create_root() -> tk.Tk:
    """Create the root Tkinter window with optional drag-and-drop support.

    Attempts to create a TkinterDnD window for drag-and-drop functionality.
    Falls back to a standard Tk window if tkinterdnd2 is unavailable or fails
    to load (common on Linux/WSL systems without the tkdnd library).

    Returns:
        The root Tk window instance.
    """
    try:
        from tkinterdnd2 import TkinterDnD

        # Test if tkdnd is actually available by creating a temporary window
        root: tk.Tk = TkinterDnD.Tk()
        # If we get here, tkdnd loaded successfully - use this window
        return root
    except (ImportError, RuntimeError, tk.TclError):
        # tkinterdnd2 not available or failed to load
        # Clean up any orphaned default root window
        default_root = getattr(tk, "_default_root", None)
        if default_root is not None:
            with contextlib.suppress(tk.TclError):
                default_root.destroy()
            tk._default_root = None  # type: ignore[attr-defined]
        return tk.Tk()


def main() -> None:
    """Launch the Taximate GUI application."""
    root = _create_root()
    app = TaximateGUI(root)
    app.run()


if __name__ == "__main__":
    main()
