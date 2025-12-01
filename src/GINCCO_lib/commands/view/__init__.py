"""
CLI entry for 'gincco view' command.

This package wraps the viewer logic. It re-exports:
- register_subparser(subparser)
- main(args)

from view.py so that GINCCO_lib.cli can discover and call them.
"""

from .view import register_subparser, main

__all__ = ["register_subparser", "main"]
