#!/usr/bin/env bash
# Sorceress gates on a rig blend (default work/rig_v5.blend): wrist swing, hand stretch (G5), contacts (G6), skirt
# panels poke, soles, jerk. Usage: TOK=<lease> scripts/gates.sh [blend]
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
B=${1:-$here/work/rig_v5.blend}
A="Standing Walking Running Attack Cast Hit Death Fidget"
for s in "gate_wrist.py $B $A" "g5_hand_stretch.py $B $A" "g6_contacts.py $B $A" "g6_skirt_poke.py $B Walking Running Attack Cast Hit Death Fidget" \
         "sole_probe.py $B $A" "jerk_probe.py $B $A"; do
  echo "=== $s" | cut -c1-60; "$here/scripts/step.sh" $s
done
