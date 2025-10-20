
#!/bin/bash
# update_gincco.sh

# Define the branch name as a variable
name_dev="developing_ver0.5"

# Check if branch exists locally
if git show-ref --verify --quiet "refs/heads/$name_dev"; then
    echo "Branch '$name_dev' already exists locally."
else
    echo "Branch '$name_dev' does not exist — creating it now..."
    git checkout -b "$name_dev"
fi

# Step 1: push changes to GitHub
git add --all
git commit -m "update"
git push -u origin "$name_dev"

# Step 2: reinstall package from GitHub branch (force reinstall)
pip install --force-reinstall --no-deps "git+https://github.com/duytung/GINCCO_lib.git@$name_dev"

echo "Done! Branch '$name_dev' pushed and package reinstalled."





