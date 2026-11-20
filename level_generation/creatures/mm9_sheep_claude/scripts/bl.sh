#!/usr/bin/env bash
# usage: bl.sh <token> <script> args...: run a Blender script under the lease, print its non-noise log lines
cd /home/pjasicek/github/OpenYAMM
T=$1; shift
out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1); rc=$?
L=$(echo "$out" | sed -n 's/^Blender log: //p')
echo "$out" | grep -v '^Blender log'
grep -v -E "Saved:|^(Fra:|Time:|Blender quit|Read prefs|  Time:|Info: |Data are loaded|\s*$)|^Blender [0-9]|^Warning: Unable|^Color management|^Writing:|Read blend| INFO: " "$L" | tail -${TAILN:-25}
echo "LOG $L rc=$rc"
exit $rc
