#!/usr/bin/env python3
"""Rebuild stream: the audit's numbers for one re-measured model, the same way aggregate.py + score.py compute them
(attack motion ratio against the MM9 biped/other median from table.json, worst live-region deformation beyond Standing,
worst hand-inside share over the bound roles).
Usage: rebuild_measure.py <motion json> <body: biped|other> role=clip ... (roles as actors.yml: standing, walking, run,
attack_melee, attack_ranged, cast, hit, fidget, dying)"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import aggregate  # noqa: E402
motion = json.loads(Path(sys.argv[1]).read_text()); body = sys.argv[2]
roles = dict(a.split('=', 1) for a in sys.argv[3:])
s = aggregate.clip_summary(motion, roles)
models = json.loads((HERE / 'table.json').read_text())['models']
NOT = {'mm9_icky', 'mm9_lobberpod'}
rows = [r for r in models.values() if r['mm9'] and r['body'] == body and r['model'] not in NOT and 'attack_melee' in r['combat']
        and r['combat']['attack_melee']['clip'].lower() not in ('standing', 'fidget', 'walking')]
rb = {k: sorted(r['combat']['attack_melee'][k] for r in rows)[len(rows) // 2] for k in ('amp_p90', 'body_share', 'peak_speed')}
a = s['combat'].get('attack_melee')
ratio = (a['amp_p90'] / rb['amp_p90'] + a['body_share'] / rb['body_share'] + a['peak_speed'] / rb['peak_speed']) / 3 if a else None
print(json.dumps({'motion_ratio': round(ratio, 2) if ratio else None, 'attack': {k: a[k] for k in ('clip', 'amp_p90', 'body_share', 'peak_speed', 'torso_turn_deg', 'length_s')} if a else None,
                  'mm9_median': rb, 'deform_worst': s['deform_worst'], 'hand_worst': s['hand_worst'], 'loop_pops': s['loop_pops']}, indent=1))
