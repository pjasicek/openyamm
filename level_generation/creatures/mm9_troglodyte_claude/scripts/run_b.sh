#!/bin/bash
# Blender step. scripts/run_b.sh <script> args (absolute or project-relative paths), from the project folder
P=$PWD; S=$1; shift; cd /home/pjasicek/github/OpenYAMM
out=$(env -u PYTHONPATH tools/run_creature_blender.sh --token be3ecdfca5fa4ec5b09123d1327bc520 level_generation/creatures/mm9_troglodyte_claude/scripts/$S "$@" 2>&1); rc=$?
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
grep -E "${F:-^[A-Z]+[ _a-z]}|Traceback|Error|^  File" "$log" | cut -c1-${W:-220}; exit $rc
