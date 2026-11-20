#!/bin/bash
# Under the shared flock (repo root): flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_peasantf4_claude/scripts/bind_under_lock.sh
# Binds PeasantF4 (rows 30, 37, 42), then regenerates the MM9 tables.
set -euo pipefail
python3 level_generation/creatures/mm9_peasantf4_claude/scripts/bind_actors_pf4.py
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
