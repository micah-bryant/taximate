#!/usr/bin/env python3
"""Taximate - Self-employment tax calculation application.

This is the main entry point for the Taximate GUI application. It creates
and launches the PySide6-based GUI.

Usage:
    python main.py
    # or
    make run
"""

from src.gui import run_app


def main() -> None:
    """Launch the Taximate GUI application."""
    run_app()


if __name__ == "__main__":
    main()
