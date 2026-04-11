"""Arcnical CLI module."""

from arcnical.cli.commands import cli

# Export cli as main for entry point compatibility
main = cli

__all__ = ["cli", "main"]