import subprocess
from pathlib import Path

def register_subparser(subparser):
    subparser.add_argument("--base", required=True, help="Base RDIR directory, e.g. /tmpdir/.../SYMPHONIE/RDIR")
    subparser.add_argument("--simu", required=True, help="Simulation name, e.g. GOTEN_NOTIDE")
    subparser.add_argument("--n", type=int, default=10, help="Number of ensemble members (default=10)")
    subparser.add_argument("--copy-notebook", type=int, choices=[0, 1], default=1, help="Copy NOTEBOOK per member (1=yes, 0=no)")

def main(args):
    """Run ensemble setup Bash script through gincco CLI."""
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "setup_ensemble.sh"

    if not script_path.exists():
        print(f"Error: setup script not found at {script_path}")
        return

    cmd = [
        "bash", str(script_path),
    ]

    # environment variables passed to bash
    env = {
        "BASE_DIR": args.base,
        "SIMU_NAME": args.simu,
        "N_MEMBERS": str(args.n),
        "copy_notebooks": str(args.copy_notebook)
    }

    print(f"Launching ensemble setup for {args.simu} with {args.n} members...")
    subprocess.run(cmd, check=True, env={**env, **dict(Path.home().env if hasattr(Path.home(), 'env') else {})})
    print("Ensemble setup completed.")
