#!/bin/bash
# Under the shared flock (repo root): flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_fre_claude/scripts/bind_under_lock_fre.sh
# Binds Fre (row 256), then regenerates the MM9 tables.
set -euo pipefail
python3 level_generation/creatures/mm9_fre_claude/scripts/bind_actors_fre.py
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
