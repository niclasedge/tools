#!/usr/bin/env python3
"""
Main entry point for diagram_agent module.

Usage:
    python -m diagram_agent "Your diagram description"
    python -m diagram_agent --interactive
"""

from .cli import main

if __name__ == "__main__":
    main()
