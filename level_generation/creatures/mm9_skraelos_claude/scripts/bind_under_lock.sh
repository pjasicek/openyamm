#!/bin/bash
# Under the shared flock (repo root): flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_skraelos_claude/scripts/bind_under_lock.sh
# Binds Skraelos (row 257), then regenerates the body overrides and the MM9 tables.
set -euo pipefail
python3 level_generation/creatures/mm9_skraelos_claude/scripts/bind_actors_sk.py
python3 tools/mm9_import_discovery/mm9_monster_bodies.py --write-overrides 2>&1 | tail -2
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
