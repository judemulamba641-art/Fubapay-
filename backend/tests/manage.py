#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks
FubaPay Backend - Manage Entry Point
"""

import os
import sys
from pathlib import Path


def load_env():
    """
    Load environment variables from .env file if present
    """
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / ".env"

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ.setdefault(key, value)


def main():
    """Run administrative tasks."""

    # Load .env variables
    load_env()

    # Default settings module
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed "
            "and available on your PYTHONPATH environment variable? "
            "Did you forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
