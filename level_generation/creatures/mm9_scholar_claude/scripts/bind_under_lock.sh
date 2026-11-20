#!/bin/bash
# Under the shared flock (repo root): flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_scholar_claude/scripts/bind_under_lock.sh
set -euo pipefail
python3 level_generation/creatures/mm9_scholar_claude/scripts/bind_actors_sc.py
python3 tools/mm9_import_discovery/mm9_monster_bodies.py --write-overrides 2>&1 | tail -2
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
