#!/usr/bin/env bash
# The contact sheet of every Chasm of the Dead prop built here (review renders from scripts/review.py: LOD0 front,
# three-quarter, side, behind-above, below, then LOD1/LOD2 three-quarter) -> review/props_sheet.png, with the
# Anskram Keep's contact_sheet.sh run in this project's directory.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$HERE/../mm9_anskramkeep_claude/scripts/contact_sheet.sh"
# its HERE is the directory above the script's: run a copy of its body from here (sed swaps only that line)
bash <(sed "s#^HERE=.*#HERE=\"$HERE\"#" "$SCRIPT")
