#!/usr/bin/env python3
"""Taximate - Self-employment tax calculation application.

This is the main entry point for the Taximate GUI application. It creates
and launches the PySide6-based GUI for calculating self-employment taxes,
including support for home office and car deductions.

Disclaimer:
    This application is for informational purposes only and does not constitute
    financial, tax, or legal advice. Consult a qualified tax professional.

Usage:
    python main.py
    # or
    make run
"""

from taximate.gui import run_app


def main() -> None:
    """Launch the Taximate GUI application."""
    run_app()


if __name__ == "__main__":
    main()
