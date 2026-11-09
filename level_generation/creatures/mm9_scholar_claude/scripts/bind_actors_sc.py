#!/usr/bin/env python3
"""Append or replace the Scholars' bindings in assets_dev/worlds/mm9/models/actors.yml and their rows in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_scholar_claude'; END = '# <<< mm9_scholar_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
SW, SR = os.environ.get('STRIDE_W', '1.2'), os.environ.get('STRIDE_R', '1.92')
BLOCK = BEGIN + """
# MM9 Bembridge Scholars (level_generation/creatures/mm9_scholar_claude): SCHOLAR.abc, one Meshy body (robe with stole, long hair and beard,
# soft cap) on SCHOLAR.abc's Bip01 skeleton (eight robe chains, beard and hair chains keyed as MM9 keys them, MPFB male hands with 15 finger
# bones per side) and its own clips, whole model mirrored to true handedness. One body paint with a robe ramp per tier (scholar1 navy,
# scholar3 mid blue), a head colour per tier (face, hair, beard, cap: two different men). Rows run basecrawl.scr, which plays no clip by
# name; no DAT object places the Scholars in the extracted maps (thjorgard holds only Scholarpromo.scr). MM9's event: Hattack1 Rattack 0.35 s.
"""
for row, name, skin, label in ((274, 'Scholar', 'sc_a', 'skin scholar1 (copper-bearded man)'), (275, 'Master Scholar', 'sc_b', 'skin scholar3 (white-bearded old man)')):
    BLOCK += f"""# {name}: row {row}, scholar.abc, {label}
- descriptor: MM9 {row} {name}
  model: worlds/mm9/models/mm9_scholar.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {SW}
    run_stride_length: {SR}
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.35}}
      attack_ranged: {{impact: 0.35}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackMelee
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    cower: Cower
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_scholar'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] not in ('274', '275')]
lines += ['274\t292\tScholar (scholar.abc, scholar1 skin, basecrawl.scr, Bembridge Scholar A); 3D model mm9_scholar, tier sc_a',
          '275\t294\tMaster Scholar (scholar.abc, scholar3 skin, basecrawl.scr, Bembridge Scholar B); 3D model mm9_scholar, tier sc_b']
tmp = t + '.tmp_scholar'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND rows 274, 275')
