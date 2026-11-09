#!/usr/bin/env bash
# Revert the material pass: reinstall the pre-pass source GLBs from backup_pre_material_pass/ with
# tools/install_model.py (source in assets_source plus its cooked runtime copy).
# Usage: revert.sh [name ...]   names with or without .glb, e.g. mm6_kni mm6_gob2.glb
# Without names: every backup whose bytes differ from the installed source (unchanged models are not re-cooked).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../../../.." && pwd)"
backups="$here/backup_pre_material_pass"
models="$root/assets_source/worlds/mm6/models"
names=()
if [ "$#" -gt 0 ]; then
    for name in "$@"; do
        names+=("${name%.glb}")
    done
else
    for backup in "$backups"/*.glb; do
        name="$(basename "$backup" .glb)"
        if ! cmp -s "$backup" "$models/$name.glb"; then
            names+=("$name")
        fi
    done
fi
if [ "${#names[@]}" -eq 0 ]; then
    echo "nothing to revert: every installed source matches its backup"
    exit 0
fi
cd "$root"
for name in "${names[@]}"; do
    if [ ! -f "$backups/$name.glb" ]; then
        echo "no backup for $name" >&2
        exit 1
    fi
    echo "reverting $name"
    python3 tools/install_model.py "$backups/$name.glb" --world mm6 --name "$name.glb"
done
