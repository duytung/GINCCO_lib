"""
CLI entry for the 'gincco view' command.

The heavy Tk/Basemap viewer modules are imported only when the command runs,
so `gincco --help` and unrelated commands do not require a working GUI/map stack.
"""

HELP = "open the experimental NetCDF viewer"


def register_subparser(subparser):
    subparser.add_argument(
        "filename",
        help="Path to data file (NetCDF).",
    )
    subparser.add_argument(
        "--grid",
        dest="gridfile",
        default=None,
        help="Path to grid file (default: try to find 'grid.nc' near the data file).",
    )


def main(args):
    from .view import main as view_main

    view_main(args)


__all__ = ["register_subparser", "main"]
