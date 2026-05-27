# GINCCOpy Project Context

This repository contains the `GINCCO_lib` Python package.

## Project Shape

- Main package: `src/GINCCO_lib`
- CLI entrypoint: `GINCCO_lib.cli:main`
- Console command: `gincco`
- Developer notes: `src/GINCCO_lib/README_DEV.md`
- User documentation: `docs/`
- Examples: `examples/`

## Working Conventions

- Prefer the existing modular CLI pattern: command modules live under `src/GINCCO_lib/commands/`.
- New CLI commands should define `register_subparser(subparser)` and `main(args)`.
- Keep package compatibility with the Python version declared in `pyproject.toml`.
- Avoid unrelated refactors when changing scientific I/O, plotting, or command behavior.
- Use the repo documentation and examples as the source of truth for public behavior.

## Current Memory

- No prior chat transcript is stored in this repo.
- If future work produces important decisions, paths, or known issues, add them here under a dated note.
