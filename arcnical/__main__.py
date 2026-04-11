"""
Entry point for 'python -m arcnical' command.

This file enables running Arcnical as a module:
  python -m arcnical analyze ./repo
  python -m arcnical eval ./repo
  python -m arcnical config --show
"""

from arcnical.cli.commands import cli


if __name__ == "__main__":
    cli()
