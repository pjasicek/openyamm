#!/usr/bin/env python3
"""Lancer and Forgemaster skin colours (user decision 2026-10-24, claude_shared/kreegan_skin.py): lancer_a bronze olive,
lancer_b teal, lancer_c charcoal, forgemaster soot (highlights lifted on the dark two). Rewrites only the skin region
(R of the body mask) of textures/lancer_ramps.json and textures/forge_ramps.json; the harness, plate, gold and glow
ramps stay. Every variant takes the luminance spread of lancer_a, which is never lifted, so a rerun gives the same
ramps. Then: runtime.py variants, far, finish (README "Rebuild from the measured master")."""
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import kreegan_skin as ks

TARGET = {'lancer_a': ks.SKIN['lancer']['a'], 'lancer_b': ks.SKIN['lancer']['b'], 'lancer_c': ks.SKIN['lancer']['c'],
          'forgemaster': ks.BOSS['forgemaster']}
for name in ('lancer_ramps.json', 'forge_ramps.json'):
    path = P / 'textures' / name
    config = json.loads(path.read_text())
    body = next(m for m in config['materials'] if m['base'] == 'HKR_A')
    spread = body['ramps']['lancer_a'][0]['colors']
    for variant, target in TARGET.items():
        skin = body['ramps'][variant][0]
        body['ramps'][variant][0] = ks.recolour({'range': skin['range'], 'colors': spread}, target)
    path.write_text(json.dumps(config, indent=2) + '\n')
    print('LANCER_SKIN', name, {v: ks.measure(body['ramps'][v][0]) for v in TARGET})
