#!/bin/bash
# bl.sh <cow|goat> <script in project scripts/> args...
cd /home/pjasicek/github/OpenYAMM
COW=29ba4377adce484f9aa6c355f3fd7af2; GOAT=c1eeb181c57e41268a1982e91e7b6b22
n=$1; shift; s=$1; shift
if [ $n = cow ]; then T=$COW; else T=$GOAT; fi
P=level_generation/creatures/mm9_${n}_claude
out=$(tools/run_creature_blender.sh --token $T $P/scripts/$s "$@" 2>&1); rc=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
echo "$out" | grep -v "^Blender log" | tail -5
if [ -n "$log" ]; then grep -E "${GREP:-^[A-Z][A-Z_0-9]+[ :]|Traceback|Error|error:|line [0-9]}" "$log" | grep -v "^Read prefs\|^Blender quit\|Color management\|^Fra:\|^Saved\|^Time" | tail -${TAILN:-60}; fi
echo "rc=$rc log=$log"
exit $rc
