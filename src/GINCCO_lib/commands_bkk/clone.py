import subprocess
from pathlib import Path

def register_subparser(subparser):
    subparser.add_argument("--model", required=True, help="Model name, e.g. SYMPHONIE")
    subparser.add_argument("--from", dest="ori", required=True, help="Source simulation name")
    subparser.add_argument("--to", dest="new", required=True, help="New simulation name")

def main(args):
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "simulation_clone.sh"
    subprocess.run([str(script_path), args.model, args.ori, args.new], check=False)
