#!/usr/bin/env python3
import argparse
import importlib
import pkgutil
import GINCCO_lib.commands as commands_pkg


def main():
    parser = argparse.ArgumentParser(
        prog="gincco",
        description="GINCCO command-line toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Dynamically load all command modules ===
    for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
        module = importlib.import_module(f"GINCCO_lib.commands.{module_name}")

        # Each command module must define a 'register_subparser' function
        if hasattr(module, "register_subparser"):
            subparser = subparsers.add_parser(module_name, help=f"{module_name} command")
            module.register_subparser(subparser)
        else:
            print(f"Warning: {module_name} has no register_subparser()")

    # === Parse arguments ===
    args = parser.parse_args()

    # Execute the chosen command
    module = importlib.import_module(f"GINCCO_lib.commands.{args.command}")
    module.main(args)
