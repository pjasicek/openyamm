#!/usr/bin/env bash
# The source project's gates on a gate copy of a GLB (gate_import.py + gate_attrs.py from ../mm7_m422_claude/work/rig_v6.blend):
# G4/G5/G6 (gates.py), cloth (coat poke, cape poke, skirt/cape stretch), armpit stretch, clasp/buckle seat drift, soles.
# Usage: TOKEN=<lease> scripts/run_gates.sh <glb relative to repo> <tag>   -> review/gates_<tag>.json, cloth_<tag>.json,
# armpit_<tag>.json, work/gates_<tag>.log
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD; glb=$1; tag=$2; export CAP=${CAP:-8G}
REA_NODE=M422 REA_GLB=$glb REA_OUT=work/gate_$tag.blend PAT="^(WELD|TRIS|PIECES)" scripts/b.sh gate_import.py
PAT="^GATEATTRS" scripts/b.sh gate_attrs.py "$P/work/gate_$tag.blend" "$P/../mm7_m422_claude/work/rig_v6.blend"
{
PAT="^GATE" scripts/b.sh gates.py "$P/work/gate_$tag.blend" $tag
PAT="^CLOTH" scripts/b.sh cloth_gates.py "$P/work/gate_$tag.blend" $tag
PAT="^ARMPIT" scripts/b.sh armpit_stretch.py "$P/work/gate_$tag.blend" $tag
PAT="^[A-Z]+ " scripts/b.sh accessory_gap.py "$P/work/gate_$tag.blend" 6,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25
STEP=0.5 PAT="^(SOLE|FOOT)" scripts/b.sh sole_probe.py "$P/work/gate_$tag.blend" Standing Walking Attack Hit Fidget Death
} 2>&1 | tee work/gates_$tag.log
