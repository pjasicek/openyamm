#!/bin/bash
# Run a project Blender script through the creature wrapper and print its log.
cd /home/pjasicek/github/OpenYAMM
out=$(tools/run_creature_blender.sh --token a87e0688e3c2442db91472fb28e900e0 "$@" 2>&1); rc=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
[ -n "$log" ] && cat "$log" | grep -v "^Read prefs\|^Warning: region\|^Blender quit\|^$" ; echo "$out" | grep -v "^Blender log"
exit $rc
