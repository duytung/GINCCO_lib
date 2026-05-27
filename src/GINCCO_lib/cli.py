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
    command_modules = {}

    # === Dynamically load all command modules ===
    for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
        module = importlib.import_module(f"GINCCO_lib.commands.{module_name}")

        # Each command module must define a 'register_subparser' function
        if hasattr(module, "register_subparser"):
            command_name = getattr(module, "COMMAND_NAME", module_name)
            command_help = getattr(module, "HELP", f"{command_name} command")
            command_modules[command_name] = module_name
            subparser = subparsers.add_parser(command_name, help=command_help)
            module.register_subparser(subparser)
        #else:
        #    print(f"Warning: {module_name} has no register_subparser()")

    # === Parse arguments ===
    args = parser.parse_args()

    # Execute the chosen command
    module_name = command_modules[args.command]
    module = importlib.import_module(f"GINCCO_lib.commands.{module_name}")
    module.main(args)
