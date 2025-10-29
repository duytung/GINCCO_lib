# 📦 GINCCO_lib Developer Notes

**Version:** 0.6  
**Maintainer:** Tung Nguyen-Duy  
**Purpose:**  
GINCCO_lib provides modular utilities for NetCDF I/O, statistical analysis, visualization, and lightweight command-line tools for simulation management and processing.

---

## 🗂️ Folder Structure Overview

src/
└── GINCCO_lib/
├── init.py
├── cli.py
├── commands/
│ ├── init.py
│ ├── clone.py
│ ├── plot.py
│ └── (other command modules)
├── scripts/
│ ├── simulation_clone.sh
│ └── (other Bash scripts)
└── README_DEV.md ← this file


### Folder Purpose

| Folder / File | Purpose |
|----------------|----------|
| `cli.py` | Main command-line interface loader. Automatically detects all subcommands in `/commands/`. |
| `commands/` | Contains modular subcommands (each defines `register_subparser()` and `main()`). |
| `scripts/` | Contains Bash scripts for system-level tasks (e.g., simulation cloning, preprocessing). |
| `README_DEV.md` | This document — developer guide for maintainers. |

---

## ⚙️ Command-Line System

### Design
GINCCO’s CLI follows this pattern:

gincco <command> [options]


Examples:
```bash
gincco clone --model SYMPHONIE --from GOT_REF2 --to GOT_REF5

Auto-discovery

cli.py automatically detects any module in GINCCO_lib/commands/ that defines:

def register_subparser(subparser): ...
def main(args): ...

No edits to cli.py are needed when adding new commands.
🧩 Adding a New Command

To add a new command (Python-based or Bash-based):

    Create a file in GINCCO_lib/commands/, e.g. preprocess.py.

    Implement these two functions:

def register_subparser(subparser):
    subparser.add_argument("--input", required=True)
    subparser.add_argument("--output", required=True)

def main(args):
    print(f"Processing {args.input} -> {args.output}")

(Optional) If using a Bash script:

    Place the .sh file under /scripts/

    Call it from main() using:

        from pathlib import Path
        import subprocess

        script = Path(__file__).resolve().parent.parent / "scripts" / "my_script.sh"
        subprocess.run([str(script), args.input, args.output], check=False)

That’s all — it will appear automatically under:

gincco --help

🧩 Packaging and Distribution
pyproject.toml Key Sections

[project.scripts]
gincco = "GINCCO_lib.cli:main"

[tool.hatch.build.targets.wheel]
include = ["src/GINCCO_lib/scripts/**", "src/GINCCO_lib/README_DEV.md"]

[tool.hatch.build.targets.sdist]
include = ["src/GINCCO_lib/scripts/**", "src/GINCCO_lib/README_DEV.md"]

    gincco → global command installed via pip

    include = [...] → ensures all .sh files and this README are bundled in the package

🧰 Adding Bash Scripts

All .sh scripts live under /scripts/ and must be executable:

chmod +x src/GINCCO_lib/scripts/my_script.sh

If you add new scripts, no need to modify pyproject.toml (thanks to the wildcard ** include).
🔍 Testing Installation
Local editable install

pip install -e .

Verify commands

gincco --help
gincco clone --model SYMPHONIE --from GOT_REF2 --to GOT_REF5

Inspect built wheel

hatch build
unzip -l dist/GINCCO_lib-0.6-py3-none-any.whl | grep scripts

You should see your .sh files and README_DEV.md listed.


🧾 License

This project is released under the GNU General Public License v3 (GPL-3.0-or-later).
See LICENSE file for full details.