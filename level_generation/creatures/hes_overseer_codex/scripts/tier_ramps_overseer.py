#!/usr/bin/env python3
"""Overseer skin colours (user decision 2026-10-24, claude_shared/kreegan_skin.py): ov_a indigo, ov_b verdigris,
ov_c ember, ov_krav ash grey, ov_ghulkat bronze. Rewrites only the skin ramps of textures/overseer_ramps.json (body
Demon_A and head DemonHead_A, mask R); horns, claws, wing membranes, equipment, sash, weapons and glow stay. Every
variant takes the luminance spread of ov_a, which is never lifted, so a rerun gives the same ramps; the head follows
the body's brightness scale, so it keeps its relation to the body. The shared export/hes_kreegan_winged.glb keeps its
own variants (the Nobles round picks their colours): do not republish it (publish_shared.py) after this.
Then: materials_preview.py, finish_lods.py hes_overseer .55,.30,.16, validate_finish.py, viewer_tiers.py."""
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import kreegan_skin as ks

TARGET = {'ov_a': ks.SKIN['overseer']['a'], 'ov_b': ks.SKIN['overseer']['b'], 'ov_c': ks.SKIN['overseer']['c'],
          'ov_krav': ks.BOSS['krav'], 'ov_ghulkat': ks.BOSS['ghulkat']}
path = P / 'textures/overseer_ramps.json'
config = json.loads(path.read_text())
body = next(m for m in config['materials'] if m['base'] == 'Demon_A')
head = next(m for m in config['materials'] if m['base'] == 'DemonHead_A')
body_spread = body['ramps']['ov_a'][0]
head_spread = head['ramps']['ov_a'][0]
for variant, target in TARGET.items():
    skin = body['ramps'][variant][0]
    body['ramps'][variant][0] = ks.recolour({'range': skin['range'], 'colors': body_spread['colors']}, target)
    face = head['ramps'][variant][0]
    head['ramps'][variant][0] = ks.recolour({'range': face['range'], 'colors': head_spread['colors']}, target,
                                            reference=body_spread)
path.write_text(json.dumps(config, indent=2) + '\n')
print('OVERSEER_SKIN', {v: (ks.measure(body['ramps'][v][0]), ks.measure(head['ramps'][v][0])) for v in TARGET})
