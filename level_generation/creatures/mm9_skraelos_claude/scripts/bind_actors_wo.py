#!/usr/bin/env python3
"""Append or replace Igrid's binding in assets_dev/worlds/mm9/models/actors.yml and her row in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_wyrdold_claude'; END = '# <<< mm9_wyrdold_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Igrid, Wyrde of the Known (row 263, wyrd_old.abc + wyrdold.dtx; level_generation/creatures/mm9_wyrdold_claude): a new Meshy body (hood,
# open robe with sleeves over a navy gown, grey braids) on wyrd_old's own stooped human female skeleton (Yrsa's, 73 joints, skirt and braid
# chains keyed as MM9 keys them, MPFB female hands with 15 finger bones per side) and its own clips (stand, walk, fidget1, Wince3, Die3: the
# Yrsa set), whole model mirrored to true handedness. One tier. basemelee.scr; no script plays a clip on her (NPC338.scr: voice and quest;
# WG_NPC334.scr toggles the Wyrdes' visibility in the win cutscene), so MM9's roles only; no attack clip: attacks play Fidget.
- descriptor: MM9 263 Wyrde of the Known (Igrid)
  model: worlds/mm9/models/mm9_wyrdold.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_W
    run_stride_length: STRIDE_R
    upper_body_root: FHP Spine1
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
    talk: Fidget
    stand: Standing
""".replace('STRIDE_W', os.environ.get('STRIDE_W', '1.55')).replace('STRIDE_R', os.environ.get('STRIDE_R', '1.58'))
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_wyrdold'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] != '263']
lines += ['263\t376\tWyrde of the Known (Igrid) (wyrd_old.abc, wyrdold skin, basemelee.scr): DAT WyrdeoftheKnown in the Hall of the Gods and Dark Passageway (NPC338.scr); 3D model mm9_wyrdold']
tmp = t + '.tmp_wyrdold'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND row 263')
