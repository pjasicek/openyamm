#!/usr/bin/env python3
"""Append or replace the Old Hag binding in assets_dev/worlds/mm9/models/actors.yml and its row in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_hag_claude'; END = '# <<< mm9_hag_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Old Hag, Hjordisa (row 245, hag.abc + hag.dtx; level_generation/creatures/mm9_hag_claude): hag.abc is Yrsa.abc with bell sleeves, no
# forehead bead band and the same clips byte for byte, so the approved Yrsa body, rig, weights and clips are reused (sleeves flared, beads
# removed) with her own 4K body and head paint. NPC132.scr plays only `die` (OnDamage) and DoRude; Yrsa's roles cover it.
- descriptor: MM9 245 Old Hag
  model: worlds/mm9/models/mm9_hag.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.5
    run_stride_length: 1.5
    look: {nodes: [FHP Neck, FHP Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Fidget
    attack_ranged: Fidget
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    talk: Fidget
"""
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_hag'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] != '245']
lines += ['245\t307\tOld Hag, Hjordisa (hag.abc = the Yrsa body with bell sleeves, hag skin; NPC132.scr): DAT object OldHag in Guberland; 3D model mm9_hag']
tmp = t + '.tmp_hag'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND row 245')
