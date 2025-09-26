#!/bin/bash
# update_gincco.sh

# Step 1: push changes to GitHub
git add --all
git commit -m "update"
git push origin developing_version

# Step 2: reinstall package from GitHub branch (force reinstall, no need to uninstall first)
pip install --force-reinstall --no-deps "git+https://github.com/duytung/GINCCO_lib.git@developing_version"
