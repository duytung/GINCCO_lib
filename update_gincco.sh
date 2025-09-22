#!/bin/bash
# update_gincco.sh

# Step 1: push changes to GitHub
git add --all
git commit -m "update"
git push origin feature/my-new-branch

# Step 2: reinstall package from GitHub branch (force reinstall, no need to uninstall first)
pip install --force-reinstall "git+https://github.com/duytung/GINCCO_lib.git@feature/my-new-branch"

