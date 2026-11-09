#!/usr/bin/env python3
"""Append or replace the Fre binding in assets_dev/worlds/mm9/models/actors.yml and its row in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_fre_claude'; END = '# <<< mm9_fre_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Fre, the goddess in the Hall of the Gods (level_generation/creatures/mm9_fre_claude): FRE.abc is the PeasantF4 body (same MM9
# PeasantFemale skeleton and binds) with a rounded hair cap instead of the hood and one braid down the back, so PeasantF4's body, rig,
# weights and the MM9 PeasantFemale library clips are reused; the hair cap and the braid are new (cap on MM9 Fre's head weights easing onto
# the neck, braid from the head onto the back). Own 4K body and head paint (red dress, brocade apron-dress panel, gold belt and cuffs,
# feather shawl; chestnut-auburn hair, gold circlet). One skin, no tiers. Clips: NPCbase.scr (Converse -> conv1-3, BaseRun Cower);
# NPC337.scr plays none. No attack clip: attacks play Fidget. Map placement (Hall of the Gods, DAT Scale 1.6) is the orchestrator's switch.
# Fre (256, Fre.abc, Fre.dtx)
- descriptor: MM9 256 Fre
  model: worlds/mm9/models/mm9_fre.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.0
    run_stride_length: 1.6
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
    cower: Cower
    conv1: Conv1
    conv2: Talk
    conv3: Conv3
    stand: Standing
"""
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_fre'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] != '256']
lines += ['256\t352\tFre (FRE.abc = PeasantF4 body with a hair cap and a braid instead of the hood, Fre skin): Hall of the Gods goddess, '
          'DAT object Fre (NPC337.scr); 3D model mm9_fre']
tmp = t + '.tmp_fre'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND MM9 256 Fre')
