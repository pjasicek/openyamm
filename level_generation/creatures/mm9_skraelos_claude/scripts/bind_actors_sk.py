#!/usr/bin/env python3
"""Append or replace Skraelos's binding in assets_dev/worlds/mm9/models/actors.yml and his row in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_skraelos_claude'; END = '# <<< mm9_skraelos_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Skraelos, the Afterworld's confessor (row 257, SKRAELOS.abc + skraelos.dtx; level_generation/creatures/mm9_skraelos_claude): a new
# Meshy body (black hood and robe, open rust tabard, bone-fang necklace) with a skull-only Meshy head and bone hands from the mesh, on
# SKRAELOS.abc's own thigh-less human female skeleton (73 joints, skirt chains), whole model mirrored to true handedness. He holds a bone staff
# (right) and a skull (left), rigid on the hands as MM9 skins them to Finger1. Clips: his own stand, walk (a glide: MM9 keys no foot
# motion), fidget1, conv1, ResurrectSpell; the PeasantFemale library (the FHP library whose joint names match his) gives run, Wince2, Die1
# (BaseName PeasantMale names a Bip01 library that cannot drive FHP joints). NPC336.scr: voice and quests only; WG_NPC336.scr loops
# stand. No attack clip: attacks play Fidget, as the Wyrdes'; ResurrectSpell is a script clip.
- descriptor: MM9 257 Skraelos
  model: worlds/mm9/models/mm9_skraelos.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_W
    run_stride_length: STRIDE_R
    look: {nodes: [FHP Neck, FHP Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    events:
      attack_melee: {impact: 1.0}
      attack_ranged: {impact: 1.0}
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
    talk: Talk
    conv1: Talk
    stand: Standing
    walk: Walking
    fidget1: Fidget
    resurrectspell: ResurrectSpell
""".replace('STRIDE_W', os.environ.get('STRIDE_W', '1.4')).replace('STRIDE_R', os.environ.get('STRIDE_R', '1.1'))
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_skraelos'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] != '257']
lines += ['257\t568\tSkraelos (SKRAELOS.abc, skraelos skin, NPCbase.scr): Afterworld confessor; DAT Skraelos in the Afterworld and the Hall of the Gods (NPC336.scr, WG_NPC336.scr); legacy Lich A as the fallback visual; 3D model mm9_skraelos']
tmp = t + '.tmp_skraelos'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND row 257')
