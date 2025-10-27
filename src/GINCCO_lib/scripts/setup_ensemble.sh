#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# Prepare directories and files for a free ensemble run.
#
# MUST be run inside the ensemble directory.
#
# Set copy_notebooks=1 if you want a separate NOTEBOOK dir per member.
# ==========================================

# === User configuration ===
BASE_DIR="/tmpdir/duytung/S271/SYMPHONIE/RDIR"   # Path to RDIR parent folder
SIMU_NAME="GOTEN_NOTIDE"                          # Base simulation name
copy_notebooks=1
N_MEMBERS=10

# === Derived paths ===
LAUNCH_DIR="${BASE_DIR}/${SIMU_NAME}"
SYMPHONIE="${LAUNCH_DIR}/S26.exe"

# === Color setup ===
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RED="\033[1;31m"
RESET="\033[0m"

# === Sanity checks ===
if [[ ! -f "$SYMPHONIE" ]]; then
    echo -e "${RED}Error:${RESET} SYMPHONIE executable not found at $SYMPHONIE"
    exit 1
fi
if [[ ! -d "$LAUNCH_DIR" ]]; then
    echo -e "${RED}Error:${RESET} LAUNCH_DIR does not exist: $LAUNCH_DIR"
    exit 1
fi

echo -e "${BLUE}>>> Preparing ensemble from base simulation '${SIMU_NAME}' with ${N_MEMBERS} members...${RESET}"

# === Create ensemble member directories ===
for memno in $(seq 1 "$N_MEMBERS"); do
    memberdir="${memno}.dir"
    echo -e "${YELLOW}--> Creating member directory: ${memberdir}${RESET}"

    mkdir -p "$memberdir"
    pushd "$memberdir" >/dev/null

    rm -rf notebook
    mkdir -p restart_output restart_outbis GRAPHIQUES OFFLINE FES2012 tmp

    ln -sf "$SYMPHONIE" .
    echo "$memno" > inputfile

    popd >/dev/null
done

echo -e "${GREEN}✓ All member directories created.${RESET}\n"

# === Copy and modify template files for each member ===
for MEMBER_NUM in $(seq 1 "$N_MEMBERS"); do
    echo -e "${BLUE}>>> Configuring member ${MEMBER_NUM}/${N_MEMBERS}${RESET}"
    pushd "${MEMBER_NUM}.dir" >/dev/null

    # -----------------------------------------
    # List of files to copy
    # -----------------------------------------
    required_files=("notebook_list.f" "job.mpi")
    optional_files=("mask_zone.txt" "submit.sh")

    # --- Copy required files ---
    for f in "${required_files[@]}"; do
        src="${LAUNCH_DIR}/${f}"
        if [[ -f "$src" ]]; then
            cp "$src" "$f"
        else
            echo -e "${RED} Error:${RESET} Required file '$f' not found in ${LAUNCH_DIR}"
            echo -e "${RED}   Stopping ensemble setup.${RESET}"
            exit 1
        fi
    done

    # --- Copy optional files ---
    for f in "${optional_files[@]}"; do
        src="${LAUNCH_DIR}/${f}"
        if [[ -f "$src" ]]; then
            cp "$src" "$f"
        else
            echo -e "${YELLOW} Warning:${RESET} Optional file '$f' not found in ${LAUNCH_DIR}, skipping."
        fi
    done

    # --- Restart link ---
    if [[ -d "${LAUNCH_DIR}/restart_ens" ]]; then
        ln -sf "${LAUNCH_DIR}/restart_ens" restart_input
    else
        echo -e "${YELLOW} Warning:${RESET} restart_ens folder not found in ${LAUNCH_DIR}"
    fi

    # -----------------------------------------
    # NOTEBOOK handling
    # -----------------------------------------
    if [[ "$copy_notebooks" -eq 1 ]]; then
        NOTEBOOK_SRC="${BASE_DIR}/${SIMU_NAME}/../../../${SIMU_NAME}/NOTEBOOK"
        if [[ -d "$NOTEBOOK_SRC" ]]; then
            cp -r "$NOTEBOOK_SRC" .
            sed -i "s|../../../${SIMU_NAME}/NOTEBOOK/|NOTEBOOK/|g" notebook_list.f
            sed -i "s|../../../${SIMU_NAME}/OFFLINE/|OFFLINE/|g" NOTEBOOK/notebook_offline.f
            sed -i "s|../../../${SIMU_NAME}/GRAPHIQUES/|GRAPHIQUES/|g" NOTEBOOK/notebook_graph
            sed -i "18s/.*/$MEMBER_NUM/" NOTEBOOK/notebook_assim_perturb
            sed -i "s|${SIMU_NAME}|ENS_${MEMBER_NUM}|g" job.mpi
        else
            echo -e "${YELLOW} Warning:${RESET} NOTEBOOK source not found at $NOTEBOOK_SRC"
        fi
    fi

    pwd
    echo -e "${GREEN}✓ Finished member ${MEMBER_NUM}${RESET}\n"
    popd >/dev/null
done

echo -e "${GREEN} Ensemble setup completed successfully for ${N_MEMBERS} members from '${SIMU_NAME}'.${RESET}"
