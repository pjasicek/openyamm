#!/bin/bash
# Blender step with grep. Usage: F='regex' scripts/run.sh script.py args...   TOKEN from work/token
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_gezzampt_claude; T=$(cat $P/work/token)
s=$1; shift
out=$(tools/run_creature_blender.sh --token $T $P/scripts/$s "$@" 2>&1 </dev/null); log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
grep -E "${F:-^[A-Z]+[ _a-z]}|Traceback|Error|^  File" "$log" | cut -c1-${W:-240}
