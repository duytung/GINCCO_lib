import subprocess
from pathlib import Path

COMMAND_NAME = "create-ensemble"
HELP = "prepare directories and files for an ensemble run"


def register_subparser(subparser):
    subparser.add_argument(
        "--rdir",
        required=True,
        help="Path to the RDIR parent folder containing the base simulation directory.",
    )
    subparser.add_argument(
        "--simu",
        required=True,
        help="Base simulation name under --rdir.",
    )
    subparser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of ensemble members to create (default: 10).",
    )
    subparser.add_argument(
        "--copy-notebooks",
        action="store_true",
        default=True,
        help="Copy one NOTEBOOK directory per member (default).",
    )
    subparser.add_argument(
        "--no-copy-notebooks",
        action="store_false",
        dest="copy_notebooks",
        help="Do not copy NOTEBOOK directories into member folders.",
    )


def main(args):
    if args.n < 1:
        raise ValueError("--n must be >= 1")

    script_path = Path(__file__).resolve().parent.parent / "scripts" / "setup_ensemble.sh"
    cmd = [
        str(script_path),
        "--rdir", args.rdir,
        "--simu", args.simu,
        "--n", str(args.n),
        "--copy-notebooks", "1" if args.copy_notebooks else "0",
    ]
    subprocess.run(cmd, check=True)
