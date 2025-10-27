#!/usr/bin/env bash
set -euo pipefail

# === Arguments ===
model_name="${1:-SYMPHONIE}"
ori="${2:-GOT_REF2}"
new="${3:-GOT_REF5}"

# === Sanity checks ===
if [[ "$ori" == "$new" ]]; then
    echo "Duplicate simulation name: '$ori' == '$new'. Exiting..."
    exit 1
fi

if [[ ! -d "$model_name" ]]; then
    echo "Model directory '$model_name' not found. Exiting..."
    exit 1
fi

# === Create new configuration ===
echo "Creating configuration directory..."
(
    cd "$model_name"
    configbox/mkconfdir "$new"
)

# === Copy and replace content in UDIR ===
echo "Copying UDIR..."
cp -r "$model_name/UDIR/$ori" "$model_name/UDIR/$new"
find "$model_name/UDIR/$new" -type f -exec sed -i "s|$ori|$new|g" {} +

# === Copy and replace content in RDIR ===
echo "Copying RDIR..."
mkdir -p "$model_name/RDIR/$new"
cp "$model_name/RDIR/$ori"/{s26*,submit*,note*,mask*} "$model_name/RDIR/$new" 2>/dev/null || true
find "$model_name/RDIR/$new" -type f -exec sed -i "s|$ori|$new|g" {} +

# === Prepare new simulation directory ===
echo "Creating simulation directory structure..."
mkdir -p "$new"/{OFFLINE,GRAPHIQUES,TIDES,LIST}

for dir in RIVERS NOTEBOOK BATHYMASK LIST; do
    if [[ -d "$ori/$dir" ]]; then
        cp -r "$ori/$dir" "$new/"
    else
        echo "Warning: $dir not found in $ori"
    fi
done

# === Update NOTEBOOK references ===
if [[ -d "$new/NOTEBOOK" ]]; then
    echo "Updating NOTEBOOK references..."
    find "$new/NOTEBOOK" -type f -exec sed -i "s|$ori|$new|g" {} +
fi

echo -e "\033[1;32mDone. Created new simulation: '$new'\033[0m"
