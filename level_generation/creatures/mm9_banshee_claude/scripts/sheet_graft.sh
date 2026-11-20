#!/bin/bash
# acceptance of the head graft: every tier, profile and from below, Standing, AttackRanged, Taunt (repo root)
P=level_generation/creatures/mm9_banshee_claude; V=level_generation/creatures/claude_shared/gltf_venv/bin/python
for t in a b c; do
 $V -W ignore $P/scripts/jshot.py $P/review/sheet_graft_banshee_$t.png 3 --tier banshee_$t ${t}g1:Standing:0:Xneck:90:0:0.6 ${t}g2:AttackRanged:0.7:Xneck:-70:0:0.6 ${t}g3:Taunt:0.35:Xneck:90:0:0.6 ${t}g4:Standing:0:Xneck:20:-40:0.6 ${t}g5:AttackRanged:0.7:Xneck:20:-40:0.6 ${t}g6:Taunt:0.35:Xneck:20:-40:0.6 2>/dev/null | tail -1 | cut -c1-60 &
done
wait
