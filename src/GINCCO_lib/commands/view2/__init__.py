"""CLI entry for the experimental redesigned NetCDF viewer."""

HELP = "open the redesigned experimental NetCDF viewer"


def register_subparser(subparser):
    subparser.add_argument(
        "filename",
        help="Path to data file (NetCDF).",
    )
    subparser.add_argument(
        "--grid",
        dest="gridfile",
        default=None,
        help="Path to grid file (default: try to find grid.nc near the data file).",
    )


def main(args):
    from .view2 import main as view2_main

    view2_main(args)


__all__ = ["register_subparser", "main"]
